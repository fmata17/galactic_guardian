import pygame


class Spaceship:
    """A class to manage the spaceship 'Moon Marauder'."""
    def __init__(self, gg_game):
        """Initialize the spaceship and its starting position."""
        self.screen = gg_game.screen
        self.screen_rect = gg_game.screen.get_rect()

        self.settings = gg_game.settings

        # loads ship image and gets its screen space
        self.image = pygame.image.load('images/spaceship.bmp')
        self.rect = self.image.get_rect()

        # starts each new ship at the bottom center of the screen
        self.rect.midbottom = self.screen_rect.midbottom

        # store a float for the ships exact horizontal position because if not specified, rect object only run integers
        self.x = float(self.rect.x)

        # movement flag to start a ship without moving
        self.moving_right = False
        self.moving_left = False

    def update_position(self):
        """Update the spaceship's position depending on the movement flags."""
        if self.moving_right:
            self.x += self.settings.spaceship_speed
        if self.moving_left:
            self.x -= self.settings.spaceship_speed

        # update the rect object from self.x
        self.rect.x = self.x

    def blitme(self):
        """Draw the spaceship at its current location."""
        self.screen.blit(self.image, self.rect)
