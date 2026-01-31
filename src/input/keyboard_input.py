"""Keyboard implementation of bilateral input interface.

Maps discrete keyboard keys to continuous bilateral input values.
Initial implementation for development and testing before BCI integration.
"""

import pygame
import time
from .input_interface import InputInterface, BilateralInput


class KeyboardInput(InputInterface):
    """Keyboard-based bilateral input.

    Maps keys to continuous values:
    - Left input: a=0.3, s=0.5, d=0.8
    - Right input: j=0.3, k=0.5, l=0.8

    When multiple keys are pressed simultaneously, uses maximum value.
    """

    def __init__(self, left_keys=None, right_keys=None):
        """Initialize keyboard input handler.

        Args:
            left_keys: Dict mapping pygame key constants to float values (0-1)
            right_keys: Dict mapping pygame key constants to float values (0-1)
        """
        # Default key mappings
        self.left_keys = left_keys or {
            pygame.K_a: 0.8,
            pygame.K_s: 0.5,
            pygame.K_d: 0.3
        }
        self.right_keys = right_keys or {
            pygame.K_j: 0.3,
            pygame.K_k: 0.5,
            pygame.K_l: 0.8
        }

        self.current_left = 0.0
        self.current_right = 0.0
        self.quit_requested = False

    def update(self, events) -> None:
        """Process keyboard events and update input state.

        Args:
            events: Pygame event list
        """
        # Check for quit events
        for event in events:
            if event.type == pygame.QUIT:
                self.quit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_requested = True

        # Get current key states
        keys = pygame.key.get_pressed()

        # Calculate left input (maximum of all pressed left keys)
        left_values = [value for key, value in self.left_keys.items() if keys[key]]
        self.current_left = max(left_values) if left_values else 0.0

        # Calculate right input (maximum of all pressed right keys)
        right_values = [value for key, value in self.right_keys.items() if keys[key]]
        self.current_right = max(right_values) if right_values else 0.0

    def get_bilateral_input(self) -> BilateralInput:
        """Get current bilateral input values.

        Returns:
            BilateralInput with current left/right activation levels
        """
        return BilateralInput(
            left=self.current_left,
            right=self.current_right,
            timestamp=time.time()
        )

    def is_quit_requested(self) -> bool:
        """Check if quit was requested (ESC key or window close).

        Returns:
            True if quit was requested
        """
        return self.quit_requested
