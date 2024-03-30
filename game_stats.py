from settings import Settings


class GameStats:
    """Track statistics for Galactic Guardian."""
    def __init__(self, gg_game):
        """Initialize statistics."""
        self.settings = gg_game.settings
        self.reset_stats()

    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.spaceships_left = self.settings.spaceship_limit
