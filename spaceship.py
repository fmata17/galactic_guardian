import pygame


class Spaceship:
    """A class to manage the spaceship 'Moon Marauder'."""
    def __init__(self, gg_game):
        """Initialize the spaceship and its starting position."""
        self.screen = gg_game.screen
        self.screen_rect = gg_game.screen.get_rect()

        # loads ship image and gets its screen space
        self.image = pygame.image.load('images/spaceship.bmp')
        self.rect = self.image.get_rect()

        # starts each new ship at the bottom center of the screen
        self.rect.midbottom = self.screen_rect.midbottom

    def blitme(self):
        """Draw the spaceship at its current location."""
        self.screen.blit(self.image, self.rect)
