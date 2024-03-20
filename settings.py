class Settings:
    """A class to define all settings for Galactic Guardian."""
    def __init__(self):
        """Initializes the game's settings for other modules."""
        # screen settings
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (54, 1, 63)

        # ship settings
        self.spaceship_speed = 5
