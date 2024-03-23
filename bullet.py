import pygame
from pygame.sprite import Sprite


class Bullet(Sprite):
    """A class to represent a bullet fired from the spaceship."""
    def __init__(self, gg_game):
        """Create a bullet object at the spaceship's current location."""
        super().__init__()
        self.screen = gg_game.screen
        self.settings = gg_game.settings
        self.color = gg_game.settings.bullet_color

        # create a bullet rect at the ship's current position.
        self.rect = pygame.Rect(0, 0, self.settings.bullet_width, self.settings.bullet_height)
        self.rect.midtop = gg_game.spaceship.rect.midtop

        # store the bullet's position as a float.
        self.y = float(self.rect.y)

    def update(self):
        """Move the bullet up the screen."""
        # update the exact position of the bullet
        self.y -= self.settings.bullet_speed
        # update the rect position
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the bullet to the screen."""
        pygame.draw.rect(self.screen, self.color, self.rect)
