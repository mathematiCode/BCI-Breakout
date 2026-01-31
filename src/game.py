"""Main game class and game loop.

Integrates all game systems and manages the game state.
"""

import pygame
import config
from src.input.input_interface import InputInterface
from src.entities.paddle import Paddle
from src.entities.ball import Ball
from src.entities.brick import BrickGrid
from src.utils.logger import DataLogger


class BreakoutGame:
    """Main Breakout game with bilateral input control.

    Manages the game loop, entity updates, collision detection,
    rendering, and data logging.
    """

    def __init__(self, input_handler: InputInterface):
        """Initialize game.

        Args:
            input_handler: InputInterface implementation for player control
        """
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.clock = pygame.time.Clock()

        # Input system (dependency injection allows easy keyboard/BCI swap)
        self.input_handler = input_handler

        # Game entities
        paddle_x = config.SCREEN_WIDTH // 2 - config.PADDLE_WIDTH // 2
        paddle_y = config.SCREEN_HEIGHT - config.PADDLE_Y_OFFSET
        self.paddle = Paddle(
            paddle_x,
            paddle_y,
            config.PADDLE_WIDTH,
            config.PADDLE_HEIGHT,
            self.screen.get_rect()
        )

        self.ball = Ball(
            config.BALL_START_X,
            config.BALL_START_Y,
            config.BALL_RADIUS
        )

        self.bricks = BrickGrid(
            rows=config.BRICK_ROWS,
            cols=config.BRICK_COLS
        )

        # Game state
        self.running = True
        self.waiting_to_start = True
        self.paused = False
        self.game_over = False
        self.testing_mode = False
        self.score = 0
        self.lives = 3

        # Data logger
        self.logger = DataLogger()

        # Font for text
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

    def run(self):
        """Main game loop."""
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(config.FPS) / 1000.0

            # Event handling
            events = pygame.event.get()
            self.input_handler.update(events)

            # Check for start/pause/restart/testing mode
            for event in events:
                if event.type == pygame.KEYDOWN:
                    # Check for Shift+Space (testing mode toggle)
                    if event.key == pygame.K_SPACE:
                        keys = pygame.key.get_pressed()
                        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                            # Toggle testing mode
                            self.testing_mode = not self.testing_mode
                            mode_status = "ENABLED" if self.testing_mode else "DISABLED"
                            print(f"\nTesting Mode {mode_status} (Infinite Lives)")
                        elif self.waiting_to_start:
                            # Start the game
                            self.waiting_to_start = False
                        elif self.game_over:
                            # Play again
                            self.reset_game()
                        else:
                            # Pause/unpause during gameplay
                            self.paused = not self.paused

            # Check quit
            if self.input_handler.is_quit_requested():
                self.running = False
                continue

            # Update game state
            if not self.waiting_to_start and not self.paused and not self.game_over:
                self.update(dt)

            # Render
            self.render()

        # Cleanup
        self.logger.save()
        stats = self.logger.get_stats()
        if stats:
            print(f"\nGame Statistics:")
            print(f"  Total time: {stats['total_time']:.1f}s")
            print(f"  Average FPS: {stats['avg_fps']:.1f}")
            print(f"  Final score: {self.score}")

        pygame.quit()

    def update(self, dt):
        """Update game state.

        Args:
            dt: Delta time in seconds
        """
        # Get bilateral input
        bilateral_input = self.input_handler.get_bilateral_input()

        # Update entities
        self.paddle.update(bilateral_input, dt)
        self.ball.update(dt)

        # Check collisions
        self.check_collisions()

        # Check if ball is lost
        if self.ball.is_lost():
            if not self.testing_mode:
                # Normal mode: lose a life
                self.lives -= 1
                self.logger.log_event('ball_lost', {'lives_remaining': self.lives})

                if self.lives <= 0:
                    self.game_over = True
                    self.logger.log_event('game_over', {'final_score': self.score})
                else:
                    self.ball.reset()
            else:
                # Testing mode: infinite lives, just reset ball
                self.logger.log_event('ball_lost_testing', {'testing_mode': True})
                self.ball.reset()

        # Check win condition
        if self.bricks.all_destroyed():
            self.game_over = True
            self.logger.log_event('level_complete', {'final_score': self.score})

        # Log frame data
        self.logger.log_frame(
            bilateral_input,
            self.paddle,
            self.ball,
            self.score,
            self.bricks.get_count()
        )

    def check_collisions(self):
        """Check and handle all collisions."""
        # Paddle-ball collision
        if self.ball.rect.colliderect(self.paddle.rect):
            # Only bounce if ball is moving downward
            if self.ball.velocity.y > 0:
                self.ball.bounce_vertical()

                # Add slight horizontal velocity based on where ball hit paddle
                paddle_center = self.paddle.rect.centerx
                ball_center = self.ball.rect.centerx
                offset = (ball_center - paddle_center) / (config.PADDLE_WIDTH / 2)
                self.ball.velocity.x += offset * 100  # Add up to ±100 px/s

                self.logger.log_event('paddle_hit', {
                    'offset': offset,
                    'ball_vx': self.ball.velocity.x
                })

        # Brick-ball collision
        for brick in self.bricks.get_active():
            if self.ball.rect.colliderect(brick.rect):
                # Determine collision direction
                # (simplified - just bounce vertically for now)
                self.ball.bounce_vertical()
                brick.destroy()
                self.score += config.BRICK_POINTS

                self.logger.log_event('brick_hit', {
                    'score': self.score,
                    'bricks_remaining': self.bricks.get_count()
                })

                # Only destroy one brick per frame
                break

    def render(self):
        """Render the game."""
        # Clear screen
        self.screen.fill(config.COLOR_BACKGROUND)

        # Draw entities
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        self.bricks.draw(self.screen)

        # Draw UI
        self.draw_ui()

        # Draw input visualization (if enabled)
        if config.SHOW_INPUT_BARS:
            self.draw_input_bars()

        # Draw overlays
        if self.waiting_to_start:
            self.draw_start_screen()
        elif self.paused:
            self.draw_pause_overlay()
        elif self.game_over:
            self.draw_game_over_overlay()

        # Update display
        pygame.display.flip()

    def draw_ui(self):
        """Draw score and lives."""
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, config.COLOR_TEXT)
        self.screen.blit(score_text, (10, 40))

        # Lives (show infinity symbol in testing mode)
        if self.testing_mode:
            lives_text = self.font.render(f"Lives: ∞", True, config.COLOR_TEXT)
        else:
            lives_text = self.font.render(f"Lives: {self.lives}", True, config.COLOR_TEXT)
        self.screen.blit(lives_text, (config.SCREEN_WIDTH - 150, 40))

        # Testing mode indicator
        if self.testing_mode:
            testing_text = self.small_font.render(
                "TESTING MODE (Infinite Lives)",
                True,
                (255, 255, 0)  # Yellow color
            )
            testing_rect = testing_text.get_rect(
                center=(config.SCREEN_WIDTH // 2, 45)
            )
            self.screen.blit(testing_text, testing_rect)

    def draw_input_bars(self):
        """Draw visual representation of bilateral inputs (for debugging)."""
        bilateral_input = self.input_handler.get_bilateral_input()

        # Left input bar (red)
        left_width = int(bilateral_input.left * config.INPUT_BAR_WIDTH)
        left_rect = pygame.Rect(
            10,
            config.INPUT_BAR_Y,
            left_width,
            config.INPUT_BAR_HEIGHT
        )
        pygame.draw.rect(self.screen, (255, 0, 0), left_rect)

        # Left input border
        border_rect = pygame.Rect(
            10,
            config.INPUT_BAR_Y,
            config.INPUT_BAR_WIDTH,
            config.INPUT_BAR_HEIGHT
        )
        pygame.draw.rect(self.screen, (100, 100, 100), border_rect, 2)

        # Left input label
        left_label = self.small_font.render(
            f"L: {bilateral_input.left:.2f}",
            True,
            config.COLOR_TEXT
        )
        self.screen.blit(left_label, (220, config.INPUT_BAR_Y - 3))

        # Right input bar (green)
        right_x = config.SCREEN_WIDTH - 10 - config.INPUT_BAR_WIDTH
        right_width = int(bilateral_input.right * config.INPUT_BAR_WIDTH)
        right_rect = pygame.Rect(
            right_x,
            config.INPUT_BAR_Y,
            right_width,
            config.INPUT_BAR_HEIGHT
        )
        pygame.draw.rect(self.screen, (0, 255, 0), right_rect)

        # Right input border
        border_rect = pygame.Rect(
            right_x,
            config.INPUT_BAR_Y,
            config.INPUT_BAR_WIDTH,
            config.INPUT_BAR_HEIGHT
        )
        pygame.draw.rect(self.screen, (100, 100, 100), border_rect, 2)

        # Right input label
        right_label = self.small_font.render(
            f"R: {bilateral_input.right:.2f}",
            True,
            config.COLOR_TEXT
        )
        self.screen.blit(right_label, (right_x - 70, config.INPUT_BAR_Y - 3))

    def draw_pause_overlay(self):
        """Draw pause screen overlay."""
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        pause_text = self.font.render("PAUSED", True, config.COLOR_TEXT)
        text_rect = pause_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        )
        self.screen.blit(pause_text, text_rect)

        resume_text = self.small_font.render(
            "Press SPACE to resume",
            True,
            config.COLOR_TEXT
        )
        resume_rect = resume_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 40)
        )
        self.screen.blit(resume_text, resume_rect)

    def draw_game_over_overlay(self):
        """Draw game over screen overlay."""
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Determine win or lose
        if self.bricks.all_destroyed():
            message = "YOU WIN!"
        else:
            message = "GAME OVER"

        game_over_text = self.font.render(message, True, config.COLOR_TEXT)
        text_rect = game_over_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 20)
        )
        self.screen.blit(game_over_text, text_rect)

        score_text = self.small_font.render(
            f"Final Score: {self.score}",
            True,
            config.COLOR_TEXT
        )
        score_rect = score_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 20)
        )
        self.screen.blit(score_text, score_rect)

        play_again_text = self.small_font.render(
            "Press SPACE to Play Again",
            True,
            config.COLOR_TEXT
        )
        play_again_rect = play_again_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 50)
        )
        self.screen.blit(play_again_text, play_again_rect)

        quit_text = self.small_font.render(
            "Press ESC to Quit",
            True,
            config.COLOR_TEXT
        )
        quit_rect = quit_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 80)
        )
        self.screen.blit(quit_text, quit_rect)

    def draw_start_screen(self):
        """Draw start screen overlay."""
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title_text = self.font.render("BCI-BREAKOUT", True, config.COLOR_TEXT)
        title_rect = title_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 60)
        )
        self.screen.blit(title_text, title_rect)

        start_text = self.font.render(
            "Press SPACE to Start",
            True,
            config.COLOR_TEXT
        )
        start_rect = start_text.get_rect(
            center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        )
        self.screen.blit(start_text, start_rect)

        # Control instructions
        controls_y = config.SCREEN_HEIGHT // 2 + 50
        left_controls = self.small_font.render(
            "Left: A (0.3), S (0.5), D (0.8)",
            True,
            config.COLOR_TEXT
        )
        left_rect = left_controls.get_rect(
            center=(config.SCREEN_WIDTH // 2, controls_y)
        )
        self.screen.blit(left_controls, left_rect)

        right_controls = self.small_font.render(
            "Right: J (0.3), K (0.5), L (0.8)",
            True,
            config.COLOR_TEXT
        )
        right_rect = right_controls.get_rect(
            center=(config.SCREEN_WIDTH // 2, controls_y + 30)
        )
        self.screen.blit(right_controls, right_rect)

        # Testing mode instruction
        testing_hint = self.small_font.render(
            "Shift+Space: Toggle Testing Mode (Infinite Lives)",
            True,
            (150, 150, 150)  # Gray color for optional feature
        )
        testing_rect = testing_hint.get_rect(
            center=(config.SCREEN_WIDTH // 2, controls_y + 70)
        )
        self.screen.blit(testing_hint, testing_rect)

    def reset_game(self):
        """Reset game to initial state for playing again."""
        # Reset game state
        self.waiting_to_start = False
        self.paused = False
        self.game_over = False
        self.score = 0
        self.lives = 3

        # Reset ball
        self.ball.reset()

        # Reset paddle position
        paddle_x = config.SCREEN_WIDTH // 2 - config.PADDLE_WIDTH // 2
        self.paddle.rect.x = paddle_x
        self.paddle.velocity = 0.0

        # Reset bricks
        self.bricks.reset()

        # Clear paddle input history
        self.paddle.clear_history()

        # Create new logger for new session
        self.logger = DataLogger()
