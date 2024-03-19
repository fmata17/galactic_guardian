import sys
import pygame
from settings import Settings
from spaceship import Spaceship


class GalacticGuardian:
    """Main class to manage game resources and conduct behavior."""
    def __init__(self):
        """
        Initialize the pygame module (game).
        Create resources (timeframe clock, screen).
        Initialize the game settings for this module.
        """
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Galactic Guardian")

        self.spaceship = Spaceship(self)

    def run_game(self):
        """Start the main loop for the game to run continuously."""
        while True:
            # watches for keyboard and mouse events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            # redraws the screen each pass through the loop
            self.screen.fill(self.settings.bg_color)
            self.spaceship.blitme()

            # makes the most recently drawn screen visible
            pygame.display.flip()

            # defines the frame rate so that the clock can make the loop run this many times per second
            self.clock.tick(60)


if __name__ == "__main__":
    # makes a game instance and runs the game
    # this makes it so the instance can only be run from this module, meaning no multiple game instances
    gg = GalacticGuardian()
    gg.run_game()
