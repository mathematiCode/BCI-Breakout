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
