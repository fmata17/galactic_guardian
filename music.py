import pygame


class Music:
    """A class to manage the game sound effects."""
    def __init__(self):
        """Initialize the music sound effects."""
        self.laser_sound = pygame.mixer.Sound('resources/lasergun.mp3')
        self.alien_sound = pygame.mixer.Sound('resources/alien_blast.mp3')
        self.ship_sound = pygame.mixer.Sound('resources/ship_explosion.mp3')

    def fire_laser_sfx(self):
        """Plays the laser sound."""
        self.laser_sound.set_volume(0.2)
        self.laser_sound.play()

    def alien_hit_sfx(self):
        """Plays the alien blast sound."""
        self.alien_sound.set_volume(1)
        self.alien_sound.play()

    def ship_hit_sfx(self):
        """Plays the ship hit sound."""
        self.ship_sound.set_volume(0.8)
        self.ship_sound.play()
