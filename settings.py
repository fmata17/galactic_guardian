class Settings:
    """A class to define all settings for Galactic Guardian."""
    def __init__(self):
        """Initializes the game's settings for other modules."""
        # screen settings
        self.screen_width = 1650
        self.screen_height = 800
        self.bg_color = (54, 1, 63)

        # ship settings
        self.spaceship_speed = 4.0

        # bullet settings
        self.bullet_speed = 8.0
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = (60, 60, 60)
        self.bullets_allowed = 5

        # alien settings
        self.alien_speed = 1.0
