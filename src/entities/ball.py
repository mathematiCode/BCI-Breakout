"""Ball entity with physics and collision handling."""

import pygame
import config


class Ball:
    """Game ball with velocity-based physics.

    The ball bounces off walls, paddle, and bricks. Uses delta-time
    based updates for consistent behavior across different frame rates.
    """

    def __init__(self, x, y, radius):
        """Initialize ball.

        Args:
            x: Initial x position (center)
            y: Initial y position (center)
            radius: Ball radius in pixels
        """
        self.radius = radius
        self.rect = pygame.Rect(
            x - radius,
            y - radius,
            radius * 2,
            radius * 2
        )

        # Initial velocity (moving down and to the right)
        self.velocity = pygame.Vector2(
            config.BALL_INITIAL_SPEED,
            -config.BALL_INITIAL_SPEED
        )
        self.max_speed = config.BALL_MAX_SPEED

    def update(self, dt):
        """Update ball position.

        Args:
            dt: Delta time in seconds
        """
        # Update position based on velocity
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

        # Bounce off walls (left and right)
        if self.rect.left <= 0:
            self.rect.left = 0
            self.velocity.x = abs(self.velocity.x)
        elif self.rect.right >= config.SCREEN_WIDTH:
            self.rect.right = config.SCREEN_WIDTH
            self.velocity.x = -abs(self.velocity.x)

        # Bounce off top wall
        if self.rect.top <= 0:
            self.rect.top = 0
            self.velocity.y = abs(self.velocity.y)

        # Limit speed to prevent infinite acceleration
        speed = self.velocity.length()
        if speed > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

    def bounce_vertical(self):
        """Bounce vertically (paddle or brick collision)."""
        self.velocity.y *= -1

    def bounce_horizontal(self):
        """Bounce horizontally (brick side collision)."""
        self.velocity.x *= -1

    def is_lost(self):
        """Check if ball fell off bottom of screen.

        Returns:
            True if ball is below screen bottom
        """
        return self.rect.top > config.SCREEN_HEIGHT

    def reset(self):
        """Reset ball to starting position and velocity."""
        self.rect.centerx = config.BALL_START_X
        self.rect.centery = config.BALL_START_Y
        self.velocity = pygame.Vector2(
            config.BALL_INITIAL_SPEED,
            -config.BALL_INITIAL_SPEED
        )

    def draw(self, surface):
        """Draw ball on screen.

        Args:
            surface: Pygame surface to draw on
        """
        pygame.draw.circle(
            surface,
            config.COLOR_BALL,
            self.rect.center,
            self.radius
        )

    def get_center(self):
        """Get ball center position.

        Returns:
            Tuple of (x, y) coordinates
        """
        return self.rect.center
