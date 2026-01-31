"""BrainFlow implementation for OpenBCI Ganglion bilateral input.

Connects to OpenBCI Ganglion board via BrainFlow library and extracts
band power from two EEG channels to drive bilateral game control.

Supports multiple connection modes:
- 'dongle': Direct connection via BLED112 Bluetooth dongle
- 'streaming': Receive data from OpenBCI GUI via network streaming
- 'synthetic': Fake data for testing without hardware
"""

import time
import numpy as np
from typing import Optional

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, LogLevels
from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations

from .input_interface import InputInterface, BilateralInput
import config


class BrainFlowInput(InputInterface):
    """BrainFlow-based bilateral input using OpenBCI Ganglion.

    Extracts band power (default 10-20 Hz) from two EEG channels
    and normalizes to 0-1 range for game control.

    Supports:
    - Direct Ganglion connection via BLED112 dongle
    - Network streaming from OpenBCI GUI
    - Synthetic board for testing without hardware
    """

    def __init__(
        self,
        connection_mode: Optional[str] = None,
        serial_port: Optional[str] = None,
        stream_ip: Optional[str] = None,
        stream_port: Optional[int] = None,
        left_channel: Optional[int] = None,
        right_channel: Optional[int] = None,
    ):
        """Initialize BrainFlow input handler.

        Args:
            connection_mode: 'dongle', 'streaming', or 'synthetic'
            serial_port: COM port for BLED112 dongle (only for 'dongle' mode)
            stream_ip: IP address for network streaming (only for 'streaming' mode)
            stream_port: Port for network streaming (only for 'streaming' mode)
            left_channel: EEG channel index for left activation
            right_channel: EEG channel index for right activation
        """
        # Load from config with parameter overrides
        self.connection_mode = connection_mode or getattr(config, 'BCI_CONNECTION_MODE', 'synthetic')
        self.serial_port = serial_port if serial_port is not None else getattr(config, 'BCI_SERIAL_PORT', '')
        self.stream_ip = stream_ip if stream_ip is not None else getattr(config, 'BCI_STREAM_IP', '225.1.1.1')
        self.stream_port = stream_port if stream_port is not None else getattr(config, 'BCI_STREAM_PORT', 6677)
        self.left_channel = left_channel if left_channel is not None else config.BCI_LEFT_CHANNEL
        self.right_channel = right_channel if right_channel is not None else config.BCI_RIGHT_CHANNEL

        # Signal processing parameters
        self.sample_rate = config.BCI_SAMPLE_RATE
        self.window_size = config.BCI_WINDOW_SIZE
        self.freq_low = config.BCI_FREQ_LOW
        self.freq_high = config.BCI_FREQ_HIGH

        # Normalization parameters
        self.normalization = config.BCI_NORMALIZATION
        self.sigmoid_gain = config.BCI_SIGMOID_GAIN
        self.sigmoid_midpoint = config.BCI_SIGMOID_MIDPOINT
        self.smoothing_factor = config.BCI_SMOOTHING_FACTOR

        # State
        self.board: Optional[BoardShim] = None
        self.eeg_channels: list = []
        self.quit_requested = False

        # Smoothed values (for reducing jitter)
        self.smoothed_left = 0.0
        self.smoothed_right = 0.0

        # For calibration/debugging
        self.raw_left_history = []
        self.raw_right_history = []

        # Initialize board
        self._setup_board()

    def _setup_board(self):
        """Initialize and start the BrainFlow board."""
        # Configure logging (enable info for connection debugging)
        BoardShim.set_log_level(LogLevels.LEVEL_INFO.value)

        # Setup board parameters
        params = BrainFlowInputParams()

        if self.connection_mode == 'synthetic':
            # Synthetic board for testing without hardware
            board_id = BoardIds.SYNTHETIC_BOARD.value
            print("[BCI] Using SYNTHETIC board for testing")
            
        elif self.connection_mode == 'streaming':
            # Network streaming from OpenBCI GUI
            board_id = BoardIds.STREAMING_BOARD.value
            params.ip_address = self.stream_ip
            params.ip_port = self.stream_port
            params.master_board = BoardIds.GANGLION_BOARD.value  # Source board type
            print(f"[BCI] Connecting to network stream at {self.stream_ip}:{self.stream_port}")
            print("[BCI] Make sure OpenBCI GUI is running with BrainFlow Streamer → Network enabled")
            
        elif self.connection_mode == 'dongle':
            # Real Ganglion board via BLED112 dongle
            board_id = BoardIds.GANGLION_BOARD.value
            if not self.serial_port:
                raise ValueError("Serial port required for dongle mode. Set BCI_SERIAL_PORT in config.py")
            params.serial_port = self.serial_port
            print(f"[BCI] Connecting to Ganglion via BLED112 dongle on {self.serial_port}")
            
        else:
            raise ValueError(f"Unknown connection mode: {self.connection_mode}. Use 'dongle', 'streaming', or 'synthetic'")

        # Create board instance
        self.board = BoardShim(board_id, params)

        # Get EEG channel indices for this board type
        # For streaming board, use the source board's channel info
        source_board_id = BoardIds.GANGLION_BOARD.value if self.connection_mode == 'streaming' else board_id
        self.eeg_channels = BoardShim.get_eeg_channels(source_board_id)
        self.sample_rate = BoardShim.get_sampling_rate(source_board_id)

        print(f"[BCI] Board sample rate: {self.sample_rate} Hz")
        print(f"[BCI] EEG channels available: {self.eeg_channels}")
        print(f"[BCI] Using channel {self.left_channel} for LEFT (pin +{self.left_channel + 1}), "
              f"channel {self.right_channel} for RIGHT (pin +{self.right_channel + 1})")

        # Validate channel selection
        if self.left_channel >= len(self.eeg_channels):
            raise ValueError(f"Left channel {self.left_channel} invalid. Board has {len(self.eeg_channels)} channels.")
        if self.right_channel >= len(self.eeg_channels):
            raise ValueError(f"Right channel {self.right_channel} invalid. Board has {len(self.eeg_channels)} channels.")

        # Prepare and start streaming
        try:
            self.board.prepare_session()
            self.board.start_stream()
            print("[BCI] Stream started successfully!")

            # Wait a moment for buffer to fill
            time.sleep(0.5)

        except Exception as e:
            print(f"[BCI] ERROR: Failed to start board: {e}")
            print("[BCI] TIP: Make sure the Ganglion is powered on and dongle is connected")
            raise

    def _get_band_power(self, channel_data: np.ndarray) -> float:
        """Extract band power from a single channel.

        Args:
            channel_data: 1D array of EEG samples

        Returns:
            Band power in the configured frequency range
        """
        if len(channel_data) < self.window_size:
            return 0.0

        # Use the most recent window_size samples
        data = channel_data[-self.window_size:].copy()

        # Apply bandpass filter to isolate frequency range
        DataFilter.perform_bandpass(
            data,
            self.sample_rate,
            self.freq_low,
            self.freq_high,
            config.BCI_FILTER_ORDER,
            FilterTypes.BUTTERWORTH.value,
            0  # ripple (not used for Butterworth)
        )

        # Calculate band power using Welch's method
        # Returns tuple of (amplitudes, frequencies)
        psd = DataFilter.get_psd_welch(
            data,
            nfft=self.window_size,
            overlap=self.window_size // 2,
            sampling_rate=self.sample_rate,
            window=WindowOperations.HANNING.value
        )

        # Sum power in our frequency band
        amplitudes, frequencies = psd
        band_mask = (frequencies >= self.freq_low) & (frequencies <= self.freq_high)
        band_power = np.sum(amplitudes[band_mask])

        return float(band_power)

    def _normalize(self, value: float) -> float:
        """Normalize raw band power to 0-1 range.

        Args:
            value: Raw band power value

        Returns:
            Normalized value between 0.0 and 1.0
        """
        if self.normalization == 'sigmoid':
            # Sigmoid function: smooth S-curve mapping
            # Centers around sigmoid_midpoint, steepness controlled by sigmoid_gain
            normalized = 1.0 / (1.0 + np.exp(-self.sigmoid_gain * (value - self.sigmoid_midpoint)))

        elif self.normalization == 'log':
            # Logarithmic scaling (good for wide dynamic range)
            min_val = config.BCI_LOG_SCALE_MIN
            max_val = config.BCI_LOG_SCALE_MAX
            # Add small epsilon to avoid log(0)
            log_val = np.log1p(value)
            log_min = np.log1p(min_val)
            log_max = np.log1p(max_val)
            normalized = (log_val - log_min) / (log_max - log_min)
            normalized = np.clip(normalized, 0.0, 1.0)

        elif self.normalization == 'minmax':
            # Simple linear scaling (requires known min/max)
            min_val = config.BCI_LOG_SCALE_MIN
            max_val = config.BCI_LOG_SCALE_MAX
            normalized = (value - min_val) / (max_val - min_val)
            normalized = np.clip(normalized, 0.0, 1.0)

        else:
            # Fallback: just clamp to 0-1
            normalized = np.clip(value / 100.0, 0.0, 1.0)

        return float(normalized)

    def update(self, events) -> None:
        """Process events and update input state.

        Args:
            events: Pygame event list
        """
        import pygame

        # Check for quit events
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_requested = True

    def get_bilateral_input(self) -> BilateralInput:
        """Get current bilateral input from EEG channels.

        Returns:
            BilateralInput with normalized left/right activation levels
        """
        if self.board is None:
            return BilateralInput(left=0.0, right=0.0, timestamp=time.time())

        # Get current data from board buffer
        # Request enough samples for our analysis window
        data = self.board.get_current_board_data(self.window_size)

        if data.size == 0:
            # No data available yet
            return BilateralInput(
                left=self.smoothed_left,
                right=self.smoothed_right,
                timestamp=time.time()
            )

        # Extract EEG channels
        left_idx = self.eeg_channels[self.left_channel]
        right_idx = self.eeg_channels[self.right_channel]

        left_data = data[left_idx, :]
        right_data = data[right_idx, :]

        # Calculate band power for each channel
        raw_left = self._get_band_power(left_data)
        raw_right = self._get_band_power(right_data)

        # Store for debugging/calibration
        self.raw_left_history.append(raw_left)
        self.raw_right_history.append(raw_right)

        # Keep history bounded
        if len(self.raw_left_history) > 1000:
            self.raw_left_history = self.raw_left_history[-500:]
            self.raw_right_history = self.raw_right_history[-500:]

        # Normalize to 0-1 range
        norm_left = self._normalize(raw_left)
        norm_right = self._normalize(raw_right)

        # Apply exponential smoothing to reduce jitter
        self.smoothed_left = (
            self.smoothing_factor * norm_left +
            (1 - self.smoothing_factor) * self.smoothed_left
        )
        self.smoothed_right = (
            self.smoothing_factor * norm_right +
            (1 - self.smoothing_factor) * self.smoothed_right
        )

        return BilateralInput(
            left=self.smoothed_left,
            right=self.smoothed_right,
            timestamp=time.time()
        )

    def is_quit_requested(self) -> bool:
        """Check if quit was requested.

        Returns:
            True if quit was requested
        """
        return self.quit_requested

    def get_calibration_stats(self) -> dict:
        """Get statistics for calibration tuning.

        Returns:
            Dict with min, max, mean, std for left and right raw values
        """
        if not self.raw_left_history:
            return {}

        return {
            'left': {
                'min': np.min(self.raw_left_history),
                'max': np.max(self.raw_left_history),
                'mean': np.mean(self.raw_left_history),
                'std': np.std(self.raw_left_history),
            },
            'right': {
                'min': np.min(self.raw_right_history),
                'max': np.max(self.raw_right_history),
                'mean': np.mean(self.raw_right_history),
                'std': np.std(self.raw_right_history),
            }
        }

    def cleanup(self):
        """Stop streaming and release board resources."""
        if self.board is not None:
            try:
                # Print calibration stats for tuning
                stats = self.get_calibration_stats()
                if stats:
                    print("\n[BCI] Session Statistics (for calibration tuning):")
                    print(f"  Left channel:  min={stats['left']['min']:.2f}, max={stats['left']['max']:.2f}, "
                          f"mean={stats['left']['mean']:.2f}, std={stats['left']['std']:.2f}")
                    print(f"  Right channel: min={stats['right']['min']:.2f}, max={stats['right']['max']:.2f}, "
                          f"mean={stats['right']['mean']:.2f}, std={stats['right']['std']:.2f}")

                self.board.stop_stream()
                self.board.release_session()
                print("[BCI] Board released successfully")
            except Exception as e:
                print(f"[BCI] Warning during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
