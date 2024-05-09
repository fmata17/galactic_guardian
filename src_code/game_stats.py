from pathlib import Path
import json


class GameStats:
    """Track statistics for Galactic Guardian."""
    def __init__(self, gg_game):
        """Initialize statistics."""
        self.settings = gg_game.settings
        self.reset_stats()
        # high score is here to avoid it ever being reset
        self._load_hs_data()

    # noinspection PyAttributeOutsideInit
    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.spaceships_left = self.settings.spaceship_limit
        self.score = 0
        self.level = 1

    def _load_hs_data(self):
        """Load highscore data from file if it exists, otherwise start with 0."""
        self.hs_path = Path("highscore.json")
        if self.hs_path.exists():
            self.high_score = json.loads(self.hs_path.read_text())
        else:
            self.high_score = 0
