class Settings:
    """A class to define all settings for Galactic Guardian."""
    def __init__(self):
        """Initializes the game's static settings for other modules."""
        # screen settings
        self.screen_width = 1650
        self.screen_height = 800
        self.bg_color = (54, 1, 63)

        # spaceship settings
        # number of EXTRA lives from the starting one
        self.spaceship_limit = 2

        # bullet settings
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = (60, 60, 60)
        self.bullets_allowed = 3

        # alien settings
        self.fleet_drop_speed = 10

        # How quickly the game speeds up
        self.speedup_scale = 1.1

        # different multipliers for various starting difficulty levels
        self.medium_scale = 2
        self.hard_scale = 3

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """Initialize settings that will change during gameplay."""
        # spaceship settings
        self.spaceship_speed = 4.0

        # bullet settings
        self.bullet_speed = 5.0

        # alien settings
        self.alien_speed = 2.0

        # fleet_direction of 1 represents right while -1 represents left
        self.fleet_direction = 1

        # scoring settings
        self.alien_points = 50

    def increase_speed(self):
        """Increase speed settings."""
        self.spaceship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale

    def change_difficulty(self, difficulty):
        """Change the starting difficulty of the game"""
        if difficulty == "medium":
            self.spaceship_speed *= self.medium_scale
            self.bullet_speed *= self.medium_scale
            self.alien_speed *= self.medium_scale
        elif difficulty == "hard":
            self.spaceship_speed *= self.hard_scale
            self.bullet_speed *= self.hard_scale
            self.alien_speed *= self.hard_scale
