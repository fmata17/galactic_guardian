import json


class GameStats:
    """Track statistics for Galactic Guardian."""
    def __init__(self, gg_game):
        """Initialize statistics."""
        self.settings = gg_game.settings
        self.reset_stats()
        # high score is here to avoid it ever being reset
        self.high_score = 0

    # noinspection PyAttributeOutsideInit
    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.spaceships_left = self.settings.spaceship_limit
        self.score = 0
        self.level = 1
