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
import opik
import inspect


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
        pygame.mixer.music.load(
            "src_code/resources/stardust_danijel_zambo_background.ogg")
        pygame.mixer.music.set_volume(0.8)
        pygame.mixer.music.play(loops=-1)

        # do not use SCALED nor vsync flags for webassembly, they are causing bugs
        self.screen = pygame.display.set_mode((self.settings.screen_width,
                                               self.settings.screen_height), pygame.FULLSCREEN)

        self.dummy_screen = pygame.Surface((self.settings.dummy_width,
                                            self.settings.dummy_height))

        pygame.display.set_caption("Galactic Guardian")

        # initialize Opik client for logging data for RL model
        self.client = opik.Opik()
        # data class for RL model
        self.data = self.GameData()
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
            self._convert_mouse_pos()
            self._check_events()

            if self.active_gameplay:
                self.state = self._get_state()  # here to track state after round begins
                self.spaceship.update()
                # here to track actions after drawing them on screen
                self.actions = self._get_actions()
                self._update_bullets()
                self._update_fleet()
                self.next_state = self._get_state()  # here to track consequences of actions

                # log data for RL model at the end of each frame
                self.log_modeled_data(
                    self.state, self.actions, self.next_state)

            self._update_screen()
            # defines the frame rate so that the clock can make the loop run this many times per second
            self.clock.tick(60)
            await asyncio.sleep(0)
        pygame.mixer.music.stop()
        pygame.quit()
        sys.exit()

    def _convert_mouse_pos(self):
        """Convert mouse position of screen to the positions on the dummy surface."""
        scale_factor_x = self.screen.get_size(
        )[0] / self.dummy_screen.get_size()[0]
        scale_factor_y = self.screen.get_size(
        )[1] / self.dummy_screen.get_size()[1]
        # different scale factors for each coordinate to ensure adequate scaling even
        # on different aspect ratios than the one of the dummy surface
        mouse_pos = pygame.mouse.get_pos()
        mouse_x = int(mouse_pos[0] / scale_factor_x)
        mouse_y = int(mouse_pos[1] / scale_factor_y)
        self.scaled_mouse_pos = (mouse_x, mouse_y)

    def _check_events(self):
        """Watches for keyboard and mouse events."""
        # set var to track firing to False each frame
        self.fired_bullet = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # start game at user request
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._check_easy_button(self.scaled_mouse_pos)
                self._check_medium_button(self.scaled_mouse_pos)
                self._check_hard_button(self.scaled_mouse_pos)

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

        # reset to 0 every new game
        self.reward = 0
        # calculate initial alien count as it can change with different screen sizes between rounds
        self.initial_alien_count = len(self.aliens)

        self.active_gameplay = True

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.spaceship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.spaceship.moving_left = False

    def _fire_bullet(self):
        """
        Creates a new bullet, adds it to the bullets group while only allowing a set amount at the time.
        Play laser sound effect.
        """
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            # noinspection PyTypeChecker
            self.bullets.add(new_bullet)
            self.fired_bullet = True
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
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)

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

    def _create_alien(self, x_position, y_position, id):
        """Creates a new alien and places it in the fleet."""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        new_alien.id = id  # to track aliens' positions for model
        # noinspection PyTypeChecker
        self.aliens.add(new_alien)

    def _create_fleet(self):
        """Creates a new fleet of aliens"""
        # make an alien and keep adding aliens until there is no more room in the screen
        # leave one alien's space above and next to each alien
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        self.aliens.add(alien)  # add the first alien to the group
        id = 0

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.dummy_height - 4 * alien_height):
            while current_x < (self.settings.dummy_width - 2 * alien_width):
                id += 1
                self._create_alien(current_x, current_y, id)
                current_x += 2 * alien_width

            # finish a row; reset x value, and increment y value
            current_x = alien_width
            current_y += 2 * alien_height

    def _update_fleet(self):
        """Check if the fleet is at an edge, then updates position of all aliens in the fleet."""
        self._check_fleet_edges()
        self.aliens.update()

        # type: ignore[arg-type]
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
            if alien.rect.bottom >= self.settings.dummy_height:
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
        Transforms and blits the dummy surface on the main screen.
        """
        self.dummy_screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.spaceship.blitme()
        self.aliens.draw(self.dummy_screen)

        # draw the scoreboard information
        self.scoreboard.show_score()

        # draw the play button if gameplay is inactive
        if not self.active_gameplay:
            self.easy_button.draw_button()
            self.medium_button.draw_button()
            self.hard_button.draw_button()

        # scale dummy surface
        scaled_dummy_screen = pygame.transform.scale(self.dummy_screen,
                                                     (self.settings.screen_width,
                                                      self.settings.screen_height))

        # blit scaled surface to main surface
        self.screen.blit(scaled_dummy_screen, (0, 0))

        pygame.display.update()

    def log_modeled_data(self, state, actions, next_state):
        reward = self._get_reward(state, next_state)
        done = float(not self.active_gameplay)

        # print to console
        self.data.add_data(state, actions, reward, next_state, done)
        # ERASEME!!!!!!!!!!!!!!!!!!!!!!
        message = self._build_log_message(
            state, actions, reward, next_state, done)
        print(message + "\n\n\n" + "="*80 + "\n\n")

        # # log to Opik as a trace
        # self.client.trace(
        #     project_name="galactic_guardian",
        #     name="game_output_data",
        #     metadata=self._build_metadata(
        #         state, actions, reward, next_state, done) or {},
        # )

    def _get_state(self):
        # add lives remaining
        lives = float(self.stats.spaceships_left)
        # add screen info and aliens positions
        ship_t = float(self.spaceship.rect.top)
        ship_r = float(self.spaceship.rect.right)
        ship_b = float(self.spaceship.rect.bottom)
        ship_l = float(self.spaceship.rect.left)

        aliens = []
        # get list of alien sprites to be able to track their positions and ids
        aliens_list = self.aliens.sprites()

        for i in range(self.initial_alien_count):
            alien = next(
                (alien for alien in aliens_list if alien.id == i), None)
            if alien:
                aliens.append((float(alien.id),
                               float(alien.rect.top),
                               float(alien.rect.right),
                               float(alien.rect.bottom),
                               float(alien.rect.left)))
            else:
                # add killed aliens as 0s in the state to indicate their absence instead of just leaving them out
                aliens.append((float(i), 0, 0, 0, 0))

        # group coordinates together for interpretability
        return (lives, (ship_t, ship_r, ship_b, ship_l), aliens)

    def _get_actions(self):
        # track movement and button presses separately for more accurate representation of valid in-game actions
        pressed_r = float(pygame.key.get_pressed()[pygame.K_RIGHT])
        moving_r = float(self.spaceship.moving_right)
        pressed_l = float(pygame.key.get_pressed()[pygame.K_LEFT])
        moving_l = float(self.spaceship.moving_left)
        # track actual firing for more accurate data for the model instead of just space bar presses
        pressed_space = float(pygame.key.get_pressed()[pygame.K_SPACE])
        fired_laser = float(self.fired_bullet)
        return (pressed_r, moving_r, pressed_l, moving_l, pressed_space, fired_laser)

    def _get_reward(self, curr_state, next_state):  # TODO: implement a score based reward
        if self.active_gameplay:
            self.reward += 1  # reward survival time
        else:
            self.reward -= 1000  # penalize game over

        death = curr_state[0] - next_state[0]
        self.reward -= death * 100

        killed = (len(curr_state[-1]) - len(next_state[-1]))
        self.reward += killed * 25  # reward eliminations
        return float(self.reward)

    class GameData:
        """Class to retrieve the data needed to train the RL model."""

        def __init__(self) -> None:
            self.buffer = []

        def add_data(self, state, action, reward, next_state, done):
            self.buffer.append((state, action, reward, next_state, done))

    def _build_log_message(self, state, actions, reward, next_state, done):
        log_message_pretty = inspect.cleandoc("""===== State Information =====
                                                 \tLives: {lives}, Ship Position: {ship}
                                                 \tAliens: {aliens}
                                                 ===== Action Choices =====
                                                 \tPressed Right: {p_right}, Pressed Left: {p_left}, Pressed Space: {space}
                                                 ===== Action Consequences =====
                                                 \tRight: {m_right}, Left: {m_left}, Fire: {fire}
                                                 ===== Reward Received =====
                                                 \t{reward}
                                                 ===== Next State Information =====
                                                 \tLives: {next_lives}, Ship Position: {next_ship}
                                                 \tAliens: {next_aliens}
                                                 ===== Terminal State =====
                                                 \tDone: {done}
                                                 """).format(lives=state[0],
                                                             ship=state[1],
                                                             aliens=state[2],
                                                             p_right=True if actions[0] else False,
                                                             m_right=True if actions[1] else False,
                                                             p_left=True if actions[2] else False,
                                                             m_left=True if actions[3] else False,
                                                             space=True if actions[4] else False,
                                                             fire=True if actions[5] else False,
                                                             reward=reward,
                                                             next_lives=next_state[0],
                                                             next_ship=next_state[1],
                                                             next_aliens=next_state[2],
                                                             done=True if done else False)
        return log_message_pretty

    def _build_metadata(self, state, actions, reward, next_state, done):
        metadata = {
            "state": {
                "lives": state[0],
                "ship_position": state[1],
                "aliens": state[2]
            },
            "actions": {
                "right_pressed": actions[0],
                "right_moving": actions[1],
                "left_pressed": actions[2],
                "left_moving": actions[3],
                "space_pressed": actions[4],
                "fire": actions[5]
            },
            "reward": reward,
            "next_state": {
                "lives": next_state[0],
                "ship_position": next_state[1],
                "aliens": next_state[2]
            },
            "done": done
        }
        return metadata


if __name__ == "__main__":
    # makes a game instance and runs the game
    # this makes it so the instance can only be run from this module, meaning no multiple game instances
    gg = GalacticGuardian()
    asyncio.run(gg.run_game())
