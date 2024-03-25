import pygame
from pygame.sprite import Sprite


class Alien(Sprite):
    """A class to represent a single alien in the fleet."""
    def __init__(self, gg_game):
        """Initialize the alien and set its initial position."""
        super().__init__()
        self.screen = gg_game.screen

        # load the alien image and set its rect attribute
        self.image = pygame.image.load('images/alien.bmp')
        self.rect = self.image.get_rect()

        # start each new alien at the top left of the screen with appropriate margins
        self.rect.x = self.rect.width
        self.rect.y = self.rect.height

        # store the alien's exact horizontal position
        self.x = float(self.rect.x)
