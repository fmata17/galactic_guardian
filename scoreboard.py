import pygame.font


class Scoreboard:
    """A class to report the score."""
    def __init__(self, gg_game):
        """Initialize the score keeping attribute"""
        self.screen = gg_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = gg_game.settings
        self.stats = gg_game.stats

        # font setting for displaying the information
        self.text_color = (30, 30, 30)
        self.font = pygame.font.SysFont(None, 48)

        # prep the initial score image
        self.prep_score()

    def prep_score(self):
        """Turn the score into a rendered image"""
        # turn score int to a string
        score_str = str(self.stats.score)
        # turn string into image
        self.score_image = self.font.render(score_str, True, self.text_color, self.settings.bg_color)
        # get rect of string image
        self.score_rect = self.score_image.get_rect()
        # display in the top right corner
        self.score_rect.right = self.screem_rect.right - 20
        self.score_rect.top = 20

    def show_score(self):
        """Show the score on the screen."""
        self.screen.blit(self.score_image, self.score_rect)
