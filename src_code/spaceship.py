import pygame
from pygame.sprite import Sprite


class Spaceship(Sprite):
    """A class to manage the spaceship 'Moon Marauder'."""
    def __init__(self, gg_game):
        """Initialize the spaceship and its starting position."""
        super().__init__()
        self.screen = gg_game.dummy_screen
        self.screen_rect = gg_game.dummy_screen.get_rect()

        self.settings = gg_game.settings

        # loads ship image and gets its screen space
        self.image = pygame.image.load('src_code/resources/spaceship.png')
        self.rect = self.image.get_rect()

        # starts each new ship at the bottom center of the screen
        self.rect.midbottom = (self.screen_rect.midbottom[0], (self.screen_rect.midbottom[1] - 10))

        # store a float for the ships exact horizontal position because if not specified, rect object only run integers
        self.x = float(self.rect.x)

        # movement flag to start a ship without moving
        self.moving_right = False
        self.moving_left = False

    def center_spaceship(self):
        """Center the spaceship on the screen."""
        self.rect.midbottom = (self.screen_rect.midbottom[0], (self.screen_rect.midbottom[1] - 10))
        self.x = float(self.rect.x)

    def update(self):
        """Update the spaceship's position depending on the movement flags."""
        # update the ship's x value, not the rect
        # limit the ship's movement to stay inside the screen
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.x += self.settings.spaceship_speed
        if self.moving_left and self.rect.left > 0:
            self.x -= self.settings.spaceship_speed

        # update the rect object from self.x
        self.rect.x = self.x

    def blitme(self):
        """Draw the spaceship at its current location."""
        self.screen.blit(self.image, self.rect)
