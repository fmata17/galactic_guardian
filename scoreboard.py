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
        self.font = pygame.font.SysFont(None, 60)

        # prep the initial score images
        self.prep_score()
        self.prep_high_score()

    def prep_score(self):
        """Turn the score into a rendered image"""
        # round the score
        rounded_score = round(self.stats.score, -1)
        # turn score int to a string and plug commas to separate
        score_str = f"{rounded_score:,}"
        # turn string into image
        self.score_image = self.font.render(score_str, True, self.text_color, self.settings.bg_color)
        # get rect of string image
        self.score_rect = self.score_image.get_rect()
        # display in the top right corner
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

    def check_high_score(self):
        """Check if the current score is bigger than the high score and respond accordingly"""
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.prep_high_score()

    def prep_high_score(self):
        """Make the high score a rendered image."""
        high_score = self.stats.high_score
        high_score_str = f"{high_score:,}"
        self.high_score_image = self.font.render(high_score_str, True, self.text_color, self.settings.bg_color)

        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.screen_rect.centerx
        self.high_score_rect.top = 20

    def show_score(self):
        """Show the score on the screen."""
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image, self.high_score_rect)
