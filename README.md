# BCI-Breakout

A Breakout game with continuous bilateral input control, designed for Brain-Computer Interface (BCI) research.

## Overview

Unlike traditional Breakout games with binary left/right controls, BCI-Breakout uses **continuous bilateral inputs** (floats from 0-1) for both left and right control signals. The paddle movement is determined by the **differential** between these inputs:

```
paddle_velocity = (right_input - left_input) × max_speed
```

This design allows for nuanced control and is ideal for researching bilateral motor coordination in BCI applications.

## Controls

### Keyboard (Initial Implementation)

- **Left Input:**
  - `A` = 0.3
  - `S` = 0.5
  - `D` = 0.8

- **Right Input:**
  - `J` = 0.3
  - `K` = 0.5
  - `L` = 0.8

- **Game Controls:**
  - `SPACE` - Start Game / Pause-Resume / Play Again
  - `SHIFT+SPACE` - Toggle Testing Mode (Infinite Lives)
  - `ESC` - Quit

### Control Examples

| Keys Pressed | Left Input | Right Input | Net Activation | Result |
|--------------|-----------|-------------|----------------|---------|
| A only | 0.3 | 0.0 | -0.3 | Move left slowly |
| D only | 0.8 | 0.0 | -0.8 | Move left quickly |
| L only | 0.0 | 0.8 | +0.8 | Move right quickly |
| S + K | 0.5 | 0.5 | 0.0 | Stay still |
| A + L | 0.3 | 0.8 | +0.5 | Move right moderately |
| D + L | 0.8 | 0.8 | 0.0 | Stay still (cancel out) |

## Installation

1. Ensure Python 3.9+ is installed
2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Game

```bash
python main.py
```

or

```bash
./main.py
```

## How to Play

1. **Start Screen**: When you launch the game, you'll see a start screen with control instructions. Press `SPACE` to begin.

2. **Gameplay**:
   - Use the bilateral inputs (keyboard keys) to control the paddle
   - The paddle velocity is determined by: `velocity = (right_input - left_input) × max_speed`
   - Break all bricks to win
   - Don't let the ball fall off the bottom!
   - You have 3 lives per game
   - Each brick is worth 10 points

3. **Pause**: Press `SPACE` during gameplay to pause/resume.

4. **Testing Mode**: Press `SHIFT+SPACE` to toggle testing mode (infinite lives):
   - When enabled, the ball resets automatically without losing lives
   - A yellow "TESTING MODE" indicator appears at the top of the screen
   - Lives display shows "∞" symbol
   - Perfect for practicing, testing control schemes, or demonstrating the game
   - Testing mode persists across game restarts until manually disabled

5. **Game Over**: When you lose all lives or break all bricks:
   - Your final score is displayed
   - Press `SPACE` to play again
   - Press `ESC` to quit

The visual input bars at the top of the screen (red=left, green=right) show your current input activation levels.

## Architecture

### File Structure

```
BCI-Breakout/
├── main.py                      # Entry point
├── config.py                    # Game configuration constants
├── src/
│   ├── game.py                  # Main game class and loop
│   ├── input/
│   │   ├── input_interface.py  # Abstract base class for inputs
│   │   └── keyboard_input.py   # Keyboard implementation
│   ├── entities/
│   │   ├── paddle.py           # Paddle with differential control
│   │   ├── ball.py             # Ball physics
│   │   └── brick.py            # Brick and grid manager
│   └── utils/
│       └── logger.py           # Data logging for research
```

### Key Design Features

1. **Strategy Pattern for Input**: The `InputInterface` abstraction allows seamless swapping between keyboard and BCI input sources without changing game logic.

2. **Differential Control**: Paddle velocity is proportional to `(right - left)`, creating natural bilateral competition.

3. **Smoothing & Deadzone**:
   - Exponential smoothing (α=0.15) prevents jittery movement
   - Deadzone (0.1) prevents drift when inputs are nearly equal

4. **Data Logging**: All input values, paddle/ball positions, and game events are logged to CSV for research analysis.

## Physics Parameters

Key parameters in `config.py`:

- `PADDLE_MAX_SPEED = 600` - Maximum paddle velocity (px/s)
- `PADDLE_SMOOTHING = 0.15` - Exponential smoothing factor
- `PADDLE_DEADZONE = 0.1` - Minimum net activation to move
- `BALL_INITIAL_SPEED = 220` - Ball speed (px/s)
- `FPS = 60` - Target frame rate

## Data Logging

When `ENABLE_LOGGING = True` in `config.py`, the game logs frame-by-frame data to CSV:

- Timestamp
- Left/right input values
- Net activation (right - left)
- Paddle position and velocity
- Ball position and velocity
- Score and bricks remaining

Log files are saved as `game_session_YYYYMMDD_HHMMSS.csv` in the project directory.

## Future BCI Integration

The architecture is designed for easy BCI integration:

1. Create `src/input/bci_input.py` implementing `InputInterface`
2. Read EEG channels (e.g., left/right motor cortex)
3. Apply signal processing:
   - Band-pass filtering (8-30 Hz for motor imagery)
   - Power spectral density calculation
   - Normalization to 0-1 range
4. Replace `KeyboardInput()` with `BCIInput()` in `main.py`

Example BCI libraries to consider:
- [BrainFlow](https://brainflow.org/) - Multi-device BCI library
- [MNE-Python](https://mne.tools/) - Advanced EEG signal processing
- [Lab Streaming Layer (LSL)](https://labstreaminglayer.readthedocs.io/) - Real-time data streaming

## Testing

Run control logic tests:
```bash
python /path/to/test_controls.py
```

This verifies that the differential control calculations are correct for all key combinations.

## Gameplay

- Use bilateral inputs to control the paddle
- Break all bricks to win
- Don't let the ball fall off the bottom!
- 3 lives per game
- 10 points per brick

The visual input bars at the top of the screen (red=left, green=right) help you understand your current input levels.

## Research Applications

This game enables studying:
- Bilateral motor coordination
- BCI control strategies (differential vs. sequential activation)
- Learning curves with novel control schemes
- Cognitive load in dual-task scenarios
- Comparison of keyboard baseline to BCI performance

## License

This project is open source. Feel free to use and modify for research purposes.

## Credits

Developed for BCI research. Uses [Pygame](https://www.pygame.org/) for game rendering and input handling.
