"""Game configuration constants.

Centralized configuration for easy parameter tuning.
"""

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WINDOW_TITLE = "BCI-Breakout"

# Colors
COLOR_BACKGROUND = (0, 0, 0)      # Black
COLOR_PADDLE = (255, 255, 255)     # White
COLOR_BALL = (255, 255, 255)       # White
COLOR_TEXT = (255, 255, 255)       # White

# Brick colors (one per row)
BRICK_COLORS = [
    (255, 0, 0),      # Red
    (255, 127, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 0, 255)       # Blue
]

# Keyboard mapping
KEYBOARD_LEFT_KEYS = {
    'a': 0.8,
    's': 0.5,
    'd': 0.3
}
KEYBOARD_RIGHT_KEYS = {
    'j': 0.3,
    'k': 0.5,
    'l': 0.8
}

# Paddle physics
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
PADDLE_Y_OFFSET = 50           # Distance from bottom of screen
PADDLE_MAX_SPEED = 600         # Pixels per second
PADDLE_SMOOTHING = 0.15        # Exponential smoothing factor (0-1)
PADDLE_DEADZONE = 0.1          # Minimum net activation to move

# Ball physics
BALL_RADIUS = 10
BALL_INITIAL_SPEED = 220       # Pixels per second
BALL_MAX_SPEED = 800           # Maximum speed limit
BALL_START_X = SCREEN_WIDTH // 2
BALL_START_Y = SCREEN_HEIGHT // 2

# Brick layout
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_PADDING_TOP = 60         # Distance from top of screen
BRICK_PADDING_SIDE = 60        # Distance from left/right edges
BRICK_SPACING = 5              # Gap between bricks
BRICK_HEIGHT = 20
BRICK_POINTS = 10              # Points per brick

# Data logging
ENABLE_LOGGING = True
LOG_FILE_PATH = 'game_session_{timestamp}.csv'

# Debug visualization
SHOW_INPUT_BARS = True         # Show visual bars for left/right input
INPUT_BAR_HEIGHT = 10
INPUT_BAR_WIDTH = 200
INPUT_BAR_Y = 10

# =============================================================================
# BCI Configuration (OpenBCI Ganglion via BrainFlow)
# =============================================================================

# Connection mode: 'dongle', 'streaming', or 'synthetic'
#   - 'dongle': Direct connection via BLED112 dongle (requires dongle hardware)
#   - 'streaming': Receive data from OpenBCI GUI via BrainFlow network streaming
#   - 'synthetic': Fake data for testing (no hardware needed)
BCI_CONNECTION_MODE = 'streaming'  # Change to 'dongle' if using BLED112 directly

# Dongle settings (only used if BCI_CONNECTION_MODE = 'dongle')
BCI_SERIAL_PORT = 'COM3'       # Serial port for BLED112 dongle

# Streaming settings (only used if BCI_CONNECTION_MODE = 'streaming')
# These must match the OpenBCI GUI's Networking → UDP settings
BCI_STREAM_IP = '127.0.0.1'    # Localhost (same computer)
BCI_STREAM_PORT = 12345        # Port number from OpenBCI GUI Stream 1

# Channel mapping (Ganglion has 4 channels: 0-3)
# Physical pins: +1=channel 0, +2=channel 1, +3=channel 2, +4=channel 3
BCI_LEFT_CHANNEL = 0           # Pin +1 on Ganglion → left activation
BCI_RIGHT_CHANNEL = 1          # Pin +2 on Ganglion → right activation

# Signal processing
BCI_SAMPLE_RATE = 200          # Ganglion native sample rate (Hz)
BCI_WINDOW_SIZE = 256          # Samples for FFT (~1.28 seconds at 200Hz)
BCI_FREQ_LOW = 10.0            # Lower frequency bound (Hz) - alpha band
BCI_FREQ_HIGH = 20.0           # Upper frequency bound (Hz) - low beta
BCI_FILTER_ORDER = 4           # Bandpass filter order

# Normalization (maps raw band power to 0-1 range)
BCI_NORMALIZATION = 'sigmoid'  # 'sigmoid', 'minmax', or 'log'
BCI_SIGMOID_GAIN = 0.005       # Sigmoid steepness (lower = gentler curve)
BCI_SIGMOID_MIDPOINT = 500.0   # Sigmoid center point (around your mean power)
BCI_LOG_SCALE_MIN = 0.0        # Log scale minimum (for 'log' normalization)
BCI_LOG_SCALE_MAX = 1000.0     # Log scale maximum (for 'log' normalization)

# Smoothing (reduces jitter from noisy EEG)
BCI_SMOOTHING_FACTOR = 0.3     # Exponential smoothing (0=no smoothing, 1=instant)
