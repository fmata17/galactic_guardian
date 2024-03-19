import sys
import pygame


class GalacticGuardian:
    """Main class to manage game resources and conduct."""
    def __init__(self):
        """Initialize the pygame module (game) and create resources (screen)."""
        pygame.init()

        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Galactic Guardian")

    def run_game(self):
        """Start the main loop for the game to run continuously."""
        while True:
            # watch for keyboard and mouse events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            # make the most recently drawn screen visible
            pygame.display.flip()


if __name__ == "__main__":
    # make a game instance and run the game
    ai = GalacticGuardian()
    ai.run_game()
