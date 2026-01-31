#!/usr/bin/env python3
"""BCI-Breakout: A Breakout game with continuous bilateral input control.

Entry point for the game. Uses keyboard input for initial implementation,
with architecture supporting future BCI integration.

Controls:
    Left input:  a=0.3, s=0.5, d=0.8
    Right input: j=0.3, k=0.5, l=0.8
    Paddle movement: velocity = (right - left) * max_speed

    SPACE: Pause/unpause
    ESC: Quit

For BCI integration, replace KeyboardInput with BCIInput implementation
in the main() function below.
"""

import sys
from src.input.keyboard_input import KeyboardInput
from src.game import BreakoutGame


def main():
    """Main entry point."""
    print("BCI-Breakout")
    print("=" * 50)
    print("Controls:")
    print("  Left input:  A (0.3), S (0.5), D (0.8)")
    print("  Right input: J (0.3), K (0.5), L (0.8)")
    print("  Movement: velocity = (right - left) * max_speed")
    print()
    print("  SPACE: Pause/Resume")
    print("  ESC: Quit")
    print("=" * 50)
    print()

    # Create input handler
    # To use BCI: replace with BCIInput(config.BCI_CONFIG)
    input_handler = KeyboardInput()

    # Create and run game
    game = BreakoutGame(input_handler)
    game.run()

    print("\nThanks for playing!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
