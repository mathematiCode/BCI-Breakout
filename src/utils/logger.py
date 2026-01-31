"""Data logger for research analysis.

Logs game state and input data to CSV files for
behavioral and BCI research analysis.
"""

import csv
import time
from datetime import datetime
from pathlib import Path
import config


class DataLogger:
    """Log game data for BCI research analysis.

    Logs input values, paddle state, ball state, and game events
    frame-by-frame for detailed behavioral analysis.
    """

    def __init__(self, filename=None):
        """Initialize data logger.

        Args:
            filename: Output filename (defaults to timestamped config value)
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = config.LOG_FILE_PATH.format(timestamp=timestamp)

        self.filename = filename
        self.data = []
        self.start_time = time.time()
        self.enabled = config.ENABLE_LOGGING

    def log_frame(self, bilateral_input, paddle, ball, score, bricks_remaining):
        """Log data for current frame.

        Args:
            bilateral_input: BilateralInput object
            paddle: Paddle object
            ball: Ball object
            score: Current score
            bricks_remaining: Number of bricks remaining
        """
        if not self.enabled:
            return

        self.data.append({
            'time': time.time() - self.start_time,
            'left_input': bilateral_input.left,
            'right_input': bilateral_input.right,
            'net_activation': bilateral_input.right - bilateral_input.left,
            'paddle_x': paddle.rect.x,
            'paddle_centerx': paddle.rect.centerx,
            'paddle_velocity': paddle.velocity,
            'ball_x': ball.rect.x,
            'ball_y': ball.rect.y,
            'ball_centerx': ball.rect.centerx,
            'ball_centery': ball.rect.centery,
            'ball_vx': ball.velocity.x,
            'ball_vy': ball.velocity.y,
            'score': score,
            'bricks_remaining': bricks_remaining
        })

    def log_event(self, event_type, details=None):
        """Log a game event.

        Args:
            event_type: Type of event (e.g., 'brick_hit', 'ball_lost', 'game_over')
            details: Optional dict with additional event details
        """
        if not self.enabled:
            return

        event_data = {
            'time': time.time() - self.start_time,
            'event_type': event_type,
        }
        if details:
            event_data.update(details)

        # For simplicity, we'll just print events
        # Could extend to separate event log file if needed
        print(f"[{event_data['time']:.2f}s] {event_type}: {details}")

    def save(self):
        """Save logged data to CSV file."""
        if not self.enabled or not self.data:
            return

        # Ensure directory exists
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)

        # Write to CSV
        with open(self.filename, 'w', newline='') as f:
            if self.data:
                writer = csv.DictWriter(f, fieldnames=self.data[0].keys())
                writer.writeheader()
                writer.writerows(self.data)

        print(f"\nData saved to {self.filename}")
        print(f"Total frames logged: {len(self.data)}")

    def get_stats(self):
        """Get summary statistics from logged data.

        Returns:
            Dict with summary statistics
        """
        if not self.data:
            return {}

        # Calculate some basic statistics
        total_time = self.data[-1]['time'] if self.data else 0
        avg_left = sum(d['left_input'] for d in self.data) / len(self.data)
        avg_right = sum(d['right_input'] for d in self.data) / len(self.data)

        return {
            'total_time': total_time,
            'total_frames': len(self.data),
            'avg_fps': len(self.data) / total_time if total_time > 0 else 0,
            'avg_left_input': avg_left,
            'avg_right_input': avg_right
        }
