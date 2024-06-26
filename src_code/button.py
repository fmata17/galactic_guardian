import pygame.font


class Button:
    """A class to build buttons for the game."""
    def __init__(self, gg_game, msg):
        """Initialize the button's attributes."""
        self.screen = gg_game.dummy_screen
        self.screen_rect = self.screen.get_rect()

        # set the dimensions and properties of the button
        self.width, self.height = 200, 50
        self.button_color = (0, 135, 0)
        self.text_color = (255, 255, 255)
        self.font = pygame.font.SysFont(None, 48)

        # build the button's rect object and center it
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = self.screen_rect.center

        # the message needs to be prepped only once.
        self._prep_msg(msg)

    def _prep_msg(self, msg):
        """Turn msg into a rendered image and center text on the button."""
        self.msg_image = self.font.render(msg, True, self.text_color, self.button_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def draw_button(self):
        """Draw the button on the screen and then message."""
        # Draw the button with rounded edges
        pygame.draw.rect(self.screen, self.button_color, self.rect, border_radius=20)
        # Blit the message image to the screen
        self.screen.blit(self.msg_image, self.msg_image_rect)
