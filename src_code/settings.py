import pygame


# noinspection PyAttributeOutsideInit
class Settings:
    """A class to define all settings for Galactic Guardian."""
    def __init__(self):
        """Initializes the game's static settings for other modules."""
        # get the screen size for each user's main monitor
        monitor = pygame.display.Info()
        # screen settings
        self.screen_width = monitor.current_w
        self.screen_height = monitor.current_h
        self.bg_color = (54, 1, 63)

        # spaceship settings
        # number of EXTRA lives from the starting one
        self.spaceship_limit = 3

        # bullet settings
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = (60, 60, 60)
        self.bullets_allowed = 3

        # alien settings
        self.fleet_drop_speed = 25

        # how quickly the game speeds up
        self.speedup_scale = 1.1

        # how quickly the point value of each alien increases
        self.score_increase_scale = 1.5

        # different multipliers for various starting difficulty levels
        self.medium_scale = 1.5
        self.hard_scale = 2

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """Initialize settings that will change during gameplay."""
        # spaceship settings
        self.spaceship_speed = 6.0

        # bullet settings
        self.bullet_speed = 8.0

        # alien settings
        self.alien_speed = 4.0

        # fleet_direction of 1 represents right while -1 represents left
        self.fleet_direction = 1

        # scoring settings
        self.alien_points = 50

    def increase_speed(self):
        """Increase speed of gameplay and alien points."""
        self.spaceship_speed *= self.speedup_scale
        self.bullet_speed *= self.speedup_scale
        self.alien_speed *= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_increase_scale)

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
