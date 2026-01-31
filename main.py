#!/usr/bin/env python3
"""BCI-Breakout: A Breakout game with continuous bilateral input control.

Entry point for the game. Supports keyboard input for testing and
BrainFlow/OpenBCI Ganglion for BCI control.

Usage:
    python main.py              # Keyboard input (default)
    python main.py --bci        # OpenBCI Ganglion via BrainFlow
    python main.py --synthetic  # BrainFlow synthetic board (testing)

Controls:
    Left input:  a=0.8, s=0.5, d=0.3
    Right input: j=0.3, k=0.5, l=0.8
    Paddle movement: velocity = (right - left) * max_speed

    SPACE: Start/Pause/Play Again
    SHIFT+SPACE: Toggle Testing Mode (Infinite Lives)
    Keyboard mode:
        Left input:  a=0.8, s=0.5, d=0.3
        Right input: j=0.3, k=0.5, l=0.8
    
    BCI mode:
        Left channel → left input (0-1)
        Right channel → right input (0-1)
    
    Paddle movement: velocity = (right - left) * max_speed

    SPACE: Pause/unpause (also starts game)
    ESC: Quit
"""

import sys
import argparse
from src.game import BreakoutGame


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='BCI-Breakout: Bilateral input Breakout game',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  # Play with keyboard
  python main.py --synthetic      # Test with synthetic BCI data
  python main.py --stream         # Receive from OpenBCI GUI network stream  
  python main.py --dongle COM4    # Use BLED112 dongle on COM4
        """
    )
    
    # Connection mode (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--synthetic', action='store_true',
        help='Use BrainFlow synthetic board for testing (no hardware)'
    )
    mode_group.add_argument(
        '--stream', action='store_true',
        help='Receive data from OpenBCI GUI via network streaming'
    )
    mode_group.add_argument(
        '--dongle', type=str, metavar='PORT',
        help='Use BLED112 dongle on specified COM port (e.g., COM4)'
    )
    
    # Channel configuration
    parser.add_argument(
        '--left-channel', type=int, default=None,
        help='EEG channel index for left input (0=pin +1, 1=pin +2, etc.)'
    )
    parser.add_argument(
        '--right-channel', type=int, default=None,
        help='EEG channel index for right input (0=pin +1, 1=pin +2, etc.)'
    )
    return parser.parse_args()


def create_input_handler(args):
    """Create appropriate input handler based on arguments."""
    if args.synthetic:
        # Synthetic BrainFlow board for testing
        from src.input.brainflow_input import BrainFlowInput
        return BrainFlowInput(
            connection_mode='synthetic',
            left_channel=args.left_channel,
            right_channel=args.right_channel,
        )
    elif args.stream:
        # UDP stream from OpenBCI GUI
        from src.input.udp_input import UDPInput
        return UDPInput(
            left_channel=args.left_channel,
            right_channel=args.right_channel,
        )
    elif args.dongle:
        # Direct connection via BLED112 dongle
        from src.input.brainflow_input import BrainFlowInput
        return BrainFlowInput(
            connection_mode='dongle',
            serial_port=args.dongle,
            left_channel=args.left_channel,
            right_channel=args.right_channel,
        )
    else:
        # Keyboard mode
        from src.input.keyboard_input import KeyboardInput
        return KeyboardInput()


def print_banner(input_mode: str):
    """Print startup banner with controls."""
    print()
    print("=" * 60)
    print("  BCI-Breakout")
    print("=" * 60)
    print(f"  Input Mode: {input_mode}")
    print()
    
    if input_mode == "Keyboard":
        print("  Controls:")
        print("    Left input:  A (0.8), S (0.5), D (0.3)")
        print("    Right input: J (0.3), K (0.5), L (0.8)")
        print("    Movement: velocity = (right - left) * max_speed")
    else:
        print("  BCI Control:")
        print("    Left channel  → left activation (0-1)")
        print("    Right channel → right activation (0-1)")
        print("    Movement: velocity = (right - left) * max_speed")
    
    print()
    print("  SPACE: Start / Pause / Play Again")
    print("  ESC:   Quit")
    print("=" * 60)
    print()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Determine input mode for display
    if args.synthetic:
        input_mode = "BrainFlow Synthetic (Testing)"
    elif args.stream:
        input_mode = "Network Stream (OpenBCI GUI)"
    elif args.dongle:
        input_mode = f"OpenBCI Ganglion (Dongle on {args.dongle})"
    else:
        input_mode = "Keyboard"
    
    print_banner(input_mode)
    
    try:
        # Create input handler
        input_handler = create_input_handler(args)
        
        # Create and run game
        game = BreakoutGame(input_handler)
        game.run()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        if args.stream:
            print("\nTroubleshooting tips for network streaming:")
            print("  1. Open OpenBCI GUI and connect to your Ganglion")
            print("  2. In 'BRAINFLOW STREAMER' section, click 'Network'")
            print("  3. Click 'Start Session' to begin streaming")
            print("  4. Then run: python main.py --stream")
        elif args.dongle:
            print("\nTroubleshooting tips for dongle mode:")
            print("  1. Make sure Ganglion is powered on (blue light)")
            print("  2. Check that the BLED112 dongle is plugged in")
            print("  3. Close the OpenBCI GUI if it's running")
            print("  4. Verify the COM port in Device Manager")
        return 1
    
    print("\nThanks for playing!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
