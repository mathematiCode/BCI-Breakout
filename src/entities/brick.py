"""Brick entities and grid manager."""

import pygame
import config


class Brick:
    """Individual brick that can be destroyed by the ball."""

    def __init__(self, x, y, width, height, color):
        """Initialize brick.

        Args:
            x: X position
            y: Y position
            width: Brick width
            height: Brick height
            color: RGB tuple for brick color
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.active = True
        self.health = 1

    def destroy(self):
        """Mark brick as destroyed."""
        self.active = False

    def draw(self, surface):
        """Draw brick if active.

        Args:
            surface: Pygame surface to draw on
        """
        if self.active:
            # Draw filled brick
            pygame.draw.rect(surface, self.color, self.rect)
            # Draw border
            pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)


class BrickGrid:
    """Manages the grid of bricks.

    Creates and maintains a grid of bricks with proper spacing
    and color assignment.
    """

    def __init__(self, rows=None, cols=None):
        """Initialize brick grid.

        Args:
            rows: Number of rows (defaults to config.BRICK_ROWS)
            cols: Number of columns (defaults to config.BRICK_COLS)
        """
        self.rows = rows or config.BRICK_ROWS
        self.cols = cols or config.BRICK_COLS
        self.bricks = []

        # Calculate brick dimensions
        total_horizontal_space = (
            config.SCREEN_WIDTH - 2 * config.BRICK_PADDING_SIDE
        )
        total_gaps = (self.cols - 1) * config.BRICK_SPACING
        brick_width = (total_horizontal_space - total_gaps) // self.cols

        # Create brick grid
        for row in range(self.rows):
            for col in range(self.cols):
                # Calculate position
                x = (
                    config.BRICK_PADDING_SIDE +
                    col * (brick_width + config.BRICK_SPACING)
                )
                y = (
                    config.BRICK_PADDING_TOP +
                    row * (config.BRICK_HEIGHT + config.BRICK_SPACING)
                )

                # Select color (cycle through colors for each row)
                color = config.BRICK_COLORS[row % len(config.BRICK_COLORS)]

                # Create brick
                brick = Brick(x, y, brick_width, config.BRICK_HEIGHT, color)
                self.bricks.append(brick)

    def get_active(self):
        """Get list of active (not destroyed) bricks.

        Returns:
            List of active Brick objects
        """
        return [brick for brick in self.bricks if brick.active]

    def all_destroyed(self):
        """Check if all bricks have been destroyed.

        Returns:
            True if no active bricks remain
        """
        return len(self.get_active()) == 0

    def draw(self, surface):
        """Draw all active bricks.

        Args:
            surface: Pygame surface to draw on
        """
        for brick in self.bricks:
            brick.draw(surface)

    def get_count(self):
        """Get count of active bricks.

        Returns:
            Number of active bricks remaining
        """
        return len(self.get_active())

    def reset(self):
        """Reset all bricks to active state."""
        for brick in self.bricks:
            brick.active = True
