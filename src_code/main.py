import asyncio
import pygame
import sys
from time import sleep
from settings import Settings
from music import Music
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from spaceship import Spaceship
from bullet import Bullet
from alien import Alien


class GalacticGuardian:
    """Main class to manage game resources and conduct behavior."""
    def __init__(self):
        """
        Initialize the pygame module (game).
        Create resources (timeframe clock, screen).
        Initialize the game settings for this module.
        """
        pygame.init()
        self.running = True
        self.active_gameplay = False
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        # load music, set volume, and play from the beginning of the program
        pygame.mixer.music.load("resources/stardust_danijel_zambo_background.wav")
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play()

        self.screen = pygame.display.set_mode((self.settings.screen_width,
                                               self.settings.screen_height),
                                              pygame.SCALED, vsync=1)
        pygame.display.set_caption("Galactic Guardian")

        self.music = Music()

        self.stats = GameStats(self)
        self.scoreboard = Scoreboard(self)

        self.spaceship = Spaceship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # make difficulty buttons
        self.easy_button = Button(self, "Easy")
        self.medium_button = Button(self, "Medium")
        self.medium_button.rect.y += 70
        self.medium_button.msg_image_rect.y += 70
        self.hard_button = Button(self, "Hard")
        self.hard_button.rect.y += 140
        self.hard_button.msg_image_rect.y += 140

    async def run_game(self):
        """Start the main loop for the game to run continuously."""
        while self.running:
            self._check_events()

            if self.active_gameplay:
                self.spaceship.update()
                self._update_bullets()
                self._update_fleet()

            self._update_screen()
            # defines the frame rate so that the clock can make the loop run this many times per second
            self.clock.tick(60)
            await asyncio.sleep(0)
        pygame.quit()
        sys.exit()

    def _check_events(self):
        """Watches for keyboard and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # start game at user request
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_easy_button(mouse_pos)
                self._check_medium_button(mouse_pos)
                self._check_hard_button(mouse_pos)

            # move spaceship to the right and left
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

    def _check_easy_button(self, mouse_pos):
        """Checks if the easy button has been clicked"""
        button_clicked = self.easy_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.active_gameplay:
            self.settings.initialize_dynamic_settings()
            self._start_game()

    def _check_medium_button(self, mouse_pos):
        """Checks if the medium button has been clicked"""
        button_clicked = self.medium_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.active_gameplay:
            self.settings.initialize_dynamic_settings()
            self.settings.change_difficulty("medium")
            self._start_game()

    def _check_hard_button(self, mouse_pos):
        """Checks if the hard button has been clicked"""
        button_clicked = self.hard_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.active_gameplay:
            self.settings.initialize_dynamic_settings()
            self.settings.change_difficulty("hard")
            self._start_game()

    def _check_keydown_events(self, event):
        """Respond to key presses."""
        if event.key == pygame.K_RIGHT:
            self.spaceship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.spaceship.moving_left = True
        elif event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_p and not self.active_gameplay:
            self._start_game()

    def _start_game(self):
        """Start a new game."""
        self.stats.reset_stats()
        self.scoreboard.prep_score()
        self.scoreboard.prep_level()
        self.scoreboard.prep_spaceships()

        # get rid of remaining bullets and aliens
        self.bullets.empty()
        self.aliens.empty()

        # create new fleet and center ship
        self._create_fleet()
        self.spaceship.center_spaceship()

        # hide mouse cursor
        pygame.mouse.set_visible(False)

        self.active_gameplay = True

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.spaceship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.spaceship.moving_left = False

    def _fire_bullet(self):
        """
        Creates a new bullet, adds it to the bullets group while only allowing three at the time.
        Play laser sound effect.
        """
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            # noinspection PyTypeChecker
            self.bullets.add(new_bullet)
            self.music.fire_laser_sfx()

    def _update_bullets(self):
        """Updates position of bullets and gets rid of old ones past the screen limit."""
        self.bullets.update()
        # use a copy because a for loop does not expect changes in the input while running
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collision()

    def _check_bullet_alien_collision(self):
        """Checks if the bullets collide with the aliens and respond appropriately."""
        # check for any bullets that have hit an alien and get rid of both, the bullet and alien
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
                # play alien hit sound effect
                self.music.alien_hit_sfx()
            self.scoreboard.prep_score()
            self.scoreboard.check_high_score()

        if not self.aliens:
            # destroy existing bullets and create new fleet
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # increase level
            self.stats.level += 1
            self.scoreboard.prep_level()

    def _create_alien(self, x_position, y_position):
        """Creates a new alien and places it in the fleet."""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        # noinspection PyTypeChecker
        self.aliens.add(new_alien)

    def _create_fleet(self):
        """Creates a new fleet of aliens"""
        # make an alien and keep adding aliens until there is no more room in the screen
        # leave one alien's space above and next to each alien
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 4 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

            # finish a row; reset x value, and increment y value
            current_x = alien_width
            current_y += 2 * alien_height

    def _update_fleet(self):
        """Check if the fleet is at an edge, then updates position of all aliens in the fleet."""
        self._check_fleet_edges()
        self.aliens.update()

        if pygame.sprite.spritecollideany(self.spaceship, self.aliens):
            self._ship_hit()

        # look for aliens hitting the bottom of the screen
        self._check_alien_bottom()

    def _ship_hit(self):
        """Responds to the spaceship being hit by an alien."""
        if self.stats.spaceships_left > 1:
            # subtract one ship to current statistic and show it on the screen
            self.stats.spaceships_left -= 1
            self.scoreboard.prep_spaceships()

            # empty bullets and aliens from screen
            self.bullets.empty()
            self.aliens.empty()

            # create new fleet and center the ship
            self._create_fleet()
            self.spaceship.center_spaceship()

            # pause and play ship hit sound effect
            self.music.ship_hit_sfx()
            sleep(3)
        else:
            self.stats.spaceships_left -= 1
            self.scoreboard.prep_spaceships()

            # play ship hit sound effect
            self.music.ship_hit_sfx()

            self.active_gameplay = False
            pygame.mouse.set_visible(True)

    def _check_fleet_edges(self):
        """Checks if the fleet has hit the left or right border of the screen and responds appropriately."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _check_alien_bottom(self):
        """Checks if any alien from the fleet has hit the bottom of the screen."""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                # treat this event the same way as if the ship got hit
                self._ship_hit()
                break

    def _change_fleet_direction(self):
        """Changes the fleet direction and drops the fleet."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        """
        Redraws the screen each pass through the loop.
        Makes the most recently drawn screen visible on the screen rect.
        """
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.spaceship.blitme()
        self.aliens.draw(self.screen)

        # draw the scoreboard information
        self.scoreboard.show_score()

        # draw the play button if gameplay is inactive
        if not self.active_gameplay:
            self.easy_button.draw_button()
            self.medium_button.draw_button()
            self.hard_button.draw_button()

        pygame.display.flip()


if __name__ == "__main__":
    # makes a game instance and runs the game
    # this makes it so the instance can only be run from this module, meaning no multiple game instances
    gg = GalacticGuardian()
    asyncio.run(gg.run_game())
