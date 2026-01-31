"""Abstract interface for bilateral input systems.

This module defines the core abstraction for all input methods,
enabling seamless switching between keyboard, BCI, and other input sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class BilateralInput:
    """Container for bilateral input values.

    Attributes:
        left: Left input activation (0.0 to 1.0)
        right: Right input activation (0.0 to 1.0)
        timestamp: Unix timestamp when input was captured
    """
    left: float
    right: float
    timestamp: float

    def __post_init__(self):
        """Validate input values are in valid range."""
        assert 0.0 <= self.left <= 1.0, f"Left input {self.left} out of range [0, 1]"
        assert 0.0 <= self.right <= 1.0, f"Right input {self.right} out of range [0, 1]"


class InputInterface(ABC):
    """Abstract base class for all input methods.

    This interface allows the game to work with any input source
    (keyboard, BCI, gamepad, etc.) without changing game logic.
    """

    @abstractmethod
    def get_bilateral_input(self) -> BilateralInput:
        """Get current left and right input values.

        Returns:
            BilateralInput with current left/right activation levels
        """
        pass

    @abstractmethod
    def update(self, events) -> None:
        """Process input events.

        Args:
            events: Pygame event list from pygame.event.get()
        """
        pass

    @abstractmethod
    def is_quit_requested(self) -> bool:
        """Check if user requested to quit the game.

        Returns:
            True if quit was requested, False otherwise
        """
        pass
