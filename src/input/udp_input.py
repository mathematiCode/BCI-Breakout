"""UDP input handler for receiving data from OpenBCI GUI.

Receives raw EEG data via UDP from the OpenBCI GUI's Networking feature
and extracts band power for bilateral game control.
"""

import socket
import struct
import threading
import time
import numpy as np
from typing import Optional
from collections import deque

from brainflow.data_filter import DataFilter, FilterTypes, WindowOperations

from .input_interface import InputInterface, BilateralInput
import config


class UDPInput(InputInterface):
    """UDP-based bilateral input from OpenBCI GUI.

    Receives EEG data streamed over UDP from OpenBCI GUI's Networking feature,
    extracts band power from two channels, and normalizes to 0-1 range.
    """

    def __init__(
        self,
        ip: Optional[str] = None,
        port: Optional[int] = None,
        left_channel: Optional[int] = None,
        right_channel: Optional[int] = None,
    ):
        """Initialize UDP input handler.

        Args:
            ip: IP address to listen on (default from config)
            port: UDP port to listen on (default from config)
            left_channel: EEG channel index for left activation
            right_channel: EEG channel index for right activation
        """
        self.ip = ip or getattr(config, 'BCI_STREAM_IP', '127.0.0.1')
        self.port = port or getattr(config, 'BCI_STREAM_PORT', 12345)
        self.left_channel = left_channel if left_channel is not None else config.BCI_LEFT_CHANNEL
        self.right_channel = right_channel if right_channel is not None else config.BCI_RIGHT_CHANNEL

        # Signal processing parameters
        self.sample_rate = getattr(config, 'BCI_SAMPLE_RATE', 200)  # Ganglion = 200 Hz
        self.window_size = getattr(config, 'BCI_WINDOW_SIZE', 256)
        self.freq_low = getattr(config, 'BCI_FREQ_LOW', 10.0)
        self.freq_high = getattr(config, 'BCI_FREQ_HIGH', 20.0)

        # Normalization parameters
        self.normalization = getattr(config, 'BCI_NORMALIZATION', 'sigmoid')
        self.sigmoid_gain = getattr(config, 'BCI_SIGMOID_GAIN', 0.1)
        self.sigmoid_midpoint = getattr(config, 'BCI_SIGMOID_MIDPOINT', 50.0)
        self.smoothing_factor = getattr(config, 'BCI_SMOOTHING_FACTOR', 0.3)

        # Data buffers (thread-safe with deque)
        self.num_channels = 4  # Ganglion has 4 channels
        self.buffers = [deque(maxlen=self.window_size) for _ in range(self.num_channels)]

        # State
        self.quit_requested = False
        self.smoothed_left = 0.0
        self.smoothed_right = 0.0
        self.running = True
        self.connected = False

        # For calibration/debugging
        self.raw_left_history = []
        self.raw_right_history = []

        # Start UDP receiver thread
        self.socket = None
        self.receiver_thread = None
        self._start_receiver()

    def _start_receiver(self):
        """Start the UDP receiver thread."""
        print(f"[UDP] Starting receiver on {self.ip}:{self.port}")
        print(f"[UDP] Using channel {self.left_channel} for LEFT, channel {self.right_channel} for RIGHT")

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.ip, self.port))
            self.socket.settimeout(0.1)  # Non-blocking with timeout

            self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receiver_thread.start()

            print("[UDP] Receiver started, waiting for data from OpenBCI GUI...")
            self.connected = True

        except Exception as e:
            print(f"[UDP] ERROR: Failed to start receiver: {e}")
            raise

    def _receive_loop(self):
        """Background thread that receives UDP packets."""
        import json
        packets_received = 0
        samples_received = 0

        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)

                try:
                    text = data.decode('utf-8').strip()
                    
                    # OpenBCI GUI sends JSON: {"type":"timeSeriesRaw","data":[[ch1...],[ch2...],[ch3...],[ch4...]]}
                    msg = json.loads(text)
                    
                    if msg.get('type') == 'timeSeriesRaw' and 'data' in msg:
                        # data is a list of channels, each channel has multiple samples
                        channels_data = msg['data']
                        
                        if packets_received == 0:
                            print(f"[UDP] Receiving JSON data! {len(channels_data)} channels, {len(channels_data[0])} samples/packet")
                        
                        # Number of samples in this packet
                        num_samples = len(channels_data[0]) if channels_data else 0
                        
                        # Add each sample to buffers
                        for sample_idx in range(num_samples):
                            for ch_idx in range(min(self.num_channels, len(channels_data))):
                                self.buffers[ch_idx].append(channels_data[ch_idx][sample_idx])
                            samples_received += 1
                        
                        packets_received += 1
                        if packets_received % 100 == 0:
                            print(f"[UDP] Packets: {packets_received}, Samples: {samples_received}, Buffer: {len(self.buffers[0])}")

                except json.JSONDecodeError:
                    # Not JSON, try comma-separated
                    try:
                        values = [float(x) for x in text.split(',') if x.strip()]
                        if len(values) >= self.num_channels:
                            for i in range(self.num_channels):
                                self.buffers[i].append(values[i])
                    except ValueError:
                        pass
                        
                except (ValueError, UnicodeDecodeError) as e:
                    if packets_received == 0:
                        print(f"[UDP] Parse error: {e}")

            except socket.timeout:
                continue
            except Exception as e:
                if self.running and packets_received < 5:
                    print(f"[UDP] Error: {e}")

    def _get_band_power(self, channel_idx: int) -> float:
        """Extract band power from a channel buffer.

        Args:
            channel_idx: Index of the channel buffer

        Returns:
            Band power in the configured frequency range
        """
        buffer = self.buffers[channel_idx]
        if len(buffer) < self.window_size // 2:
            return 0.0

        # Convert to numpy array
        data = np.array(list(buffer), dtype=np.float64)

        if len(data) < 32:  # Minimum for FFT
            return 0.0

        try:
            # Apply bandpass filter
            filtered = data.copy()
            DataFilter.perform_bandpass(
                filtered,
                self.sample_rate,
                self.freq_low,
                self.freq_high,
                4,  # filter order
                FilterTypes.BUTTERWORTH.value,
                0
            )

            # Calculate power (RMS squared)
            power = np.mean(filtered ** 2)
            return float(power)

        except Exception as e:
            # If filtering fails, return simple RMS
            return float(np.mean(data ** 2))

    def _normalize(self, value: float) -> float:
        """Normalize raw band power to 0-1 range."""
        if self.normalization == 'sigmoid':
            normalized = 1.0 / (1.0 + np.exp(-self.sigmoid_gain * (value - self.sigmoid_midpoint)))
        else:
            normalized = np.clip(value / 100.0, 0.0, 1.0)
        return float(normalized)

    def update(self, events) -> None:
        """Process events."""
        import pygame

        for event in events:
            if event.type == pygame.QUIT:
                self.quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_requested = True

    def get_bilateral_input(self) -> BilateralInput:
        """Get current bilateral input from EEG channels."""
        # Get band power for each channel
        raw_left = self._get_band_power(self.left_channel)
        raw_right = self._get_band_power(self.right_channel)

        # Store for debugging
        self.raw_left_history.append(raw_left)
        self.raw_right_history.append(raw_right)
        if len(self.raw_left_history) > 1000:
            self.raw_left_history = self.raw_left_history[-500:]
            self.raw_right_history = self.raw_right_history[-500:]

        # Normalize
        norm_left = self._normalize(raw_left)
        norm_right = self._normalize(raw_right)

        # Smooth
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
        return self.quit_requested

    def get_calibration_stats(self) -> dict:
        """Get statistics for calibration tuning."""
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
        """Stop receiver and close socket."""
        self.running = False

        stats = self.get_calibration_stats()
        if stats:
            print("\n[UDP] Session Statistics (for calibration tuning):")
            print(f"  Left channel:  min={stats['left']['min']:.2f}, max={stats['left']['max']:.2f}, "
                  f"mean={stats['left']['mean']:.2f}, std={stats['left']['std']:.2f}")
            print(f"  Right channel: min={stats['right']['min']:.2f}, max={stats['right']['max']:.2f}, "
                  f"mean={stats['right']['mean']:.2f}, std={stats['right']['std']:.2f}")

        if self.socket:
            self.socket.close()
        print("[UDP] Receiver stopped")

    def __del__(self):
        self.cleanup()
