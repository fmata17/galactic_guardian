import numpy as np
from pathlib import Path
from src_code.main import GalacticGuardian
# TODO implement opik for dev and testing


class GalacticGuardianEnv:
    """A wrapper for the Galactic Guardian game that provides an environment interface for reinforcement learning."""

    def __init__(self, mode="RL"):
        """Initialize the environment and the game."""
        self.mode = mode
        self.gg_game = GalacticGuardian(mode=self.mode)

        self.step_count = 0  # Track the number of steps taken in the current episode

        # Define a maximum number of steps per episode to prevent infinite episodes
        self.max_steps = 6000
        # Define a maximum level for the game simulation
        self.max_level = 10

        # Track the previous score to calculate delta_score for reward calculation
        self.prev_score = 0

        self.action_space = [0,  # do nothing
                             1,  # move right
                             2,  # move left
                             3,  # fire bullet
                             4,  # move right and fire bullet
                             5]  # move left and fire bullet

    def step(self, action_id=0):
        """Take an action in the environment and return the new observation, reward, done flag, and info."""
        if self.gg_game.active_gameplay:
            # ERASE ME: USED FOR DEBUGGING AND TESTING ACTION LIMITS, CONDITIONAL TEST
            # if action_id in [3, 4, 5] and len(self.gg_game.bullets) >= self.gg_game.settings.bullets_allowed:
            #     print(
            #         "Bullet limit reached! Cannot fire more bullets until some are off the screen.")

            self.step_count += 1  # Increment step count

            # Get the current observation before taking the action
            observation = self.get_observation()

            # Execute the action in the game
            self.gg_game.act(action_id)

            # Advance the game state by one tick
            self.gg_game.tick()

            # Get the next observation
            next_observation = self.get_observation()
            next_observation_processed = self.process_observation(
                next_observation)
            terminated = self._is_done()  # Check if game is over
            # Check if episode is truncated
            truncated = self._is_truncated()

            reward = self.calculate_reward(
                # Calculate reward
                observation, next_observation, (terminated or truncated))

            # Get additional info and metadata
            info = {"step_count": self.step_count}

            # Log the environment information at regular intervals
            self._logger(next_observation, freq=180, to_file=False)
            # Update previous score for the next step's delta_score calculation after logging
            #   to ensure the logged delta_score corresponds to the current step's reward calculation
            self.prev_score = next_observation["score"]

            return next_observation_processed, reward, terminated, truncated, info
        else:
            raise RuntimeError("Call reset() before step().")

    def reset(self):
        """Reset the game to start a new episode."""
        self.gg_game.reset()  # Reset the game instance
        self.step_count = 0  # Reset step count for the new episode
        observation = self.get_observation()
        info = {"step_count": self.step_count}
        # set previous score to the initial score after reset for correct delta_score calculation in the first step
        self.prev_score = observation["score"]
        return self.process_observation(observation), info

    # NOTE reward calculation is the single most critical component for a successful training
    # this is what signals the model WHAT to learn and HOW to learn it
    def calculate_reward(self, observation, next_observation, done):
        """Calculate the reward based on the change in score and other factors."""
        # Base reward for surviving a step or penalty for episode termination
        reward = 0.1 if not done else -500.0
        # Loss in remaining lives (0 or 1)
        delta_lives = observation["remaining_lives"] - \
            next_observation["remaining_lives"]
        # Change in score (delta_score)
        # TODO: consider and test removing the delta rewards
        delta_score = next_observation["score"] - observation["score"]
        # Level progression (0 or 1)
        d_level = next_observation["curr_level"] - observation["curr_level"]
        # Penalize for lost lives
        reward -= (delta_lives * 100.0)
        # Reward for score increase
        reward += (delta_score * 10.0)
        # Reward for level progression
        # 100 # not reached very often during training,
        reward += (d_level * 5000.0)
        # ATTEMPT: bigger reward for level progression to encourage it more, TEST
        return reward

    # TODO consider adding bullets in screen and max bullets in screen at any time

    def get_observation(self):
        """Get the current state of the game as an observation."""
        # For simplicity, we can return a dictionary of UNPROCESSED game state information
        observation = {
            "remaining_lives": self.gg_game.stats.spaceships_left,
            "total_lives": self.gg_game.settings.spaceship_limit,
            "ship_center_x": self.gg_game.spaceship.rect.centerx,
            "ship_center_y": self.gg_game.spaceship.rect.centery,
            "ship_width": self.gg_game.spaceship.rect.width,
            "ship_height": self.gg_game.spaceship.rect.height,
            "world_width": self.gg_game.settings.dummy_width,
            "world_height": self.gg_game.settings.dummy_height,
            "score": self.gg_game.stats.score,
            "curr_level": self.gg_game.stats.level,
            "bullet_count": len(self.gg_game.bullets)
        }

        # Add aliens info
        for i in range(self.gg_game.initial_alien_count):
            alien = next(
                (alien for alien in self.gg_game.aliens.sprites() if alien.id == i), None)
            if alien:
                observation.update({
                    f"alien_{alien.id}_center_x": alien.rect.centerx,
                    f"alien_{alien.id}_center_y": alien.rect.centery,
                    f"alien_{alien.id}_width": alien.rect.width,
                    f"alien_{alien.id}_height": alien.rect.height,
                })
            else:
                # add killed aliens as 0s in the state to indicate their absence instead of just leaving them out
                observation.update({
                    f"alien_{i}_center_x": 0,
                    f"alien_{i}_center_y": 0,
                    f"alien_{i}_width": 0,
                    f"alien_{i}_height": 0,
                })
        return observation

    def process_observation(self, observation):
        """
        Process the raw observation into a format suitable for the agent.
        Observation vector includes:
        [remaining_lives_std,       ship_center_x_std,          ship_center_y_std,      ship_width_std,
         ship_height_std,           delta_score,                level_prog,             bullet_count_std,
         alien_0_center_x_std,      alien_0_center_y_std,       alien_0_width_std,      alien_0_height_std, ...,
         alien_N_center_x_std,      alien_N_center_y_std,       alien_N_width_std,      alien_N_height_std]
        """
        remaining_lives_std = observation["remaining_lives"] / \
            observation["total_lives"]

        ship_center_x_std = observation["ship_center_x"] / \
            observation["world_width"]

        ship_center_y_std = observation["ship_center_y"] / \
            observation["world_height"]

        ship_width_std = observation["ship_width"] / \
            observation["world_width"]

        ship_height_std = observation["ship_height"] / \
            observation["world_height"]

        delta_score = observation["score"] - self.prev_score

        level_prog = min(observation["curr_level"],
                         self.max_level) / self.max_level

        bullet_count_std = observation["bullet_count"] / \
            self.gg_game.settings.bullets_allowed

        aliens = []
        for i in range(self.gg_game.initial_alien_count):
            alien_center_x_std = observation[f"alien_{i}_center_x"] / \
                observation["world_width"]
            alien_center_y_std = observation[f"alien_{i}_center_y"] / \
                observation["world_height"]
            alien_width_std = observation[f"alien_{i}_width"] / \
                observation["world_width"]
            alien_height_std = observation[f"alien_{i}_height"] / \
                observation["world_height"]
            aliens.extend([alien_center_x_std, alien_center_y_std,
                           alien_width_std, alien_height_std])

        processed_observation = np.array([remaining_lives_std, ship_center_x_std, ship_center_y_std,
                                          ship_width_std, ship_height_std, delta_score, level_prog, bullet_count_std] + aliens,
                                         dtype=np.float32)
        return processed_observation

    def _is_done(self):
        """Determine if the episode is done based on the observation."""
        return not self.gg_game.active_gameplay

    def _is_truncated(self):
        """Determine if the episode is truncated based on step count."""
        return self.step_count >= self.max_steps  # or observation["curr_level"] >= self.max_level # can also truncate based on max level, TEST

    def _logger(self, env_info, freq=60, to_file=False):
        """A simple logger to print the environment information."""
        if self.step_count % freq == 0:
            proc_env_info = self.process_observation(
                env_info)

            rem_lives, tot_lives = env_info["remaining_lives"], env_info["total_lives"]
            cur_level, tot_levels = env_info["curr_level"], self.max_level
            ship_x, ship_y = env_info["ship_center_x"], env_info["ship_center_y"]
            delta_score, total_score = proc_env_info[5], env_info["score"]
            bullet_count = env_info["bullet_count"]

            message = f"""
{"*" * 70}
Life {rem_lives}/{tot_lives}\t\tLevel {cur_level}/{tot_levels}\t\tBullets in Air: {bullet_count}/ {self.gg_game.settings.bullets_allowed}
Ship Pos: ({ship_x}, {ship_y})\t\tDelta Score: {delta_score}\t\tTotal Score: {total_score}
""".strip() + "\n"
            if to_file:  # Optionally save the log to a file
                path = Path(__file__).resolve().parent / \
                    "logs" / "runstats.txt"
                # Ensure the logs directory exists
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "a") as f:
                    f.write(message)
            print(message)
