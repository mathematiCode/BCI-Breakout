"""Paddle entity with differential bilateral control.

The paddle is controlled by two continuous inputs (left and right).
Movement is determined by the difference: velocity = (right - left) * max_speed.
"""

import pygame
from src.input.input_interface import BilateralInput
import config


class Paddle:
    """Game paddle controlled by bilateral input.

    Uses differential control: paddle velocity is proportional to
    the difference between right and left input activations.
    """

    def __init__(self, x, y, width, height, screen_bounds):
        """Initialize paddle.

        Args:
            x: Initial x position
            y: Initial y position
            width: Paddle width in pixels
            height: Paddle height in pixels
            screen_bounds: pygame.Rect defining screen boundaries
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.screen_bounds = screen_bounds

        # Physics parameters
        self.max_speed = config.PADDLE_MAX_SPEED
        self.velocity = 0.0
        self.smoothing_factor = config.PADDLE_SMOOTHING
        self.deadzone = config.PADDLE_DEADZONE

        # For research logging
        self.input_history = []

    def update(self, bilateral_input: BilateralInput, dt: float):
        """Update paddle position based on bilateral input.

        Implements differential control with smoothing and deadzone.

        Args:
            bilateral_input: Current left/right input values
            dt: Delta time in seconds
        """
        # Calculate net activation (differential control)
        net_activation = bilateral_input.right - bilateral_input.left

        # Apply deadzone to prevent drift
        if abs(net_activation) < self.deadzone:
            net_activation = 0.0

        # Calculate target velocity
        target_velocity = net_activation * self.max_speed

        # Apply exponential smoothing for fluid movement
        # Prevents jittery movement from noisy inputs
        self.velocity = (
            self.smoothing_factor * target_velocity +
            (1 - self.smoothing_factor) * self.velocity
        )

        # Update position
        self.rect.x += self.velocity * dt

        # Clamp to screen bounds
        self.rect.clamp_ip(self.screen_bounds)

        # Log for research analysis
        self.input_history.append({
            'timestamp': bilateral_input.timestamp,
            'left': bilateral_input.left,
            'right': bilateral_input.right,
            'net_activation': net_activation,
            'velocity': self.velocity,
            'position': self.rect.x
        })

    def draw(self, surface):
        """Draw paddle on screen.

        Args:
            surface: Pygame surface to draw on
        """
        pygame.draw.rect(surface, config.COLOR_PADDLE, self.rect)

    def get_input_history(self):
        """Get logged input history for data analysis.

        Returns:
            List of dicts containing input and paddle state history
        """
        return self.input_history

    def clear_history(self):
        """Clear input history to free memory."""
        self.input_history = []
