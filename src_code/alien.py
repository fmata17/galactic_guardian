import pygame
from pygame.sprite import Sprite


class Alien(Sprite):
    """A class to represent a single alien in the fleet."""
    def __init__(self, gg_game):
        """Initialize the alien and set its initial position."""
        super().__init__()
        self.screen = gg_game.dummy_screen
        self.settings = gg_game.settings

        # load the alien image and set its rect attribute
        self.pre_image = pygame.image.load('src_code/resources/alien.png')
        self.image = pygame.transform.scale(self.pre_image, (147, 76))
        self.rect = self.image.get_rect()

        # start each new alien at the top left of the screen with appropriate margins
        self.rect.x = self.rect.width
        self.rect.y = self.rect.height

        # store the alien's exact horizontal position
        self.x = float(self.rect.x)

    def check_edges(self):
        """Return True if an alien is at the edge of the screen."""
        screen_rect = self.screen.get_rect()
        return (self.rect.right >= screen_rect.right) or (self.rect.left <= 0)

    def update(self):
        """Move the alien left or right."""
        self.x += self.settings.alien_speed * self.settings.fleet_direction
        self.rect.x = self.x
