import numpy as np
from main import GalacticGuardian
# TODO implement opik for dev and testing


class GalacticGuardianEnv:
    """A wrapper for the Galactic Guardian game that provides an environment interface for reinforcement learning."""

    def __init__(self, mode="RL"):
        """Initialize the environment and the game."""
        self.mode = mode
        self.step_count = 0  # Track the number of steps taken in the current episode

        # Define a maximum number of steps per episode to prevent infinite episodes
        self.max_steps = 3000
        # Define a maximum level for the game simulation
        self.max_level = 10

        self.gg_game = GalacticGuardian(mode=self.mode)

    def step(self, action_id=0):
        """Take an action in the environment and return the new observation, reward, done flag, and info."""
        if self.gg_game.active_gameplay:
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
                next_observation, score_before=observation["score"])

            reward = self.calculate_reward(
                observation, next_observation)  # Calculate reward

            terminated = self.is_done()  # Check if game is over
            # Check if episode is truncated
            truncated = self.is_truncated(next_observation)

            # Get additional info and metadata
            info = {"step_count": self.step_count}

            return next_observation_processed, reward, terminated, truncated, info
        else:
            raise RuntimeError("Call reset() before step().")

    def reset(self):
        """Reset the game to start a new episode."""
        self.gg_game.reset()  # Reset the game instance
        self.step_count = 0  # Reset step count for the new episode
        observation = self.get_observation()
        info = {"step_count": self.step_count}
        return self.process_observation(observation), info

    def is_done(self):
        """Determine if the episode is done based on the observation."""
        return not self.gg_game.active_gameplay

    def is_truncated(self, observation):
        """Determine if the episode is truncated based on step count."""
        return self.step_count >= self.max_steps  # or observation["curr_level"] >= self.max_level # can also truncate based on max level, TEST

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

    def process_observation(self, observation, score_before=0):
        """
        Process the raw observation into a format suitable for the agent.
        Observation vector includes:
        [remaining_lives_std,       ship_center_x_std,      ship_center_y_std,      ship_width_std,
         ship_height_std,           delta_score,                level_prog,             alien_0_center_x_std,
         alien_0_center_y_std,      alien_0_width_std,      alien_0_height_std, ...,
         alien_N_center_x_std,      alien_N_center_y_std,   alien_N_width_std,      alien_N_height_std]
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

        delta_score = observation["score"] - score_before

        level_prog = min(observation["curr_level"],
                         self.max_level) / self.max_level

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
                                          ship_width_std, ship_height_std, delta_score, level_prog] + aliens,
                                         dtype=np.float32)
        return processed_observation

    def calculate_reward(self, observation, next_observation):
        """Calculate the reward based on the change in score and other factors."""
        reward = 0
        if not self.is_done():
            reward += 1  # Reward for surviving each step
        else:
            reward -= 50  # Penalty for losing the game
        # Loss in remaining lives (0 or 1)
        delta_lives = observation["remaining_lives"] - \
            next_observation["remaining_lives"]
        # Change in score (delta_score)
        # TODO: consider and test removing the delta rewards
        delta_score = next_observation["score"] - observation["score"]
        # Level progression (0 or 1)
        d_level = next_observation["curr_level"] - observation["curr_level"]
        # Penalize for lost lives
        reward -= (delta_lives * 10)
        # Reward for score increase (delta_score is at index 5)
        reward += (delta_score * 0.5)
        # Reward for level progression (level_prog is at index 6)
        reward += (d_level * 2)
        return reward


if __name__ == "__main__":
    # env = GalacticGuardianEnv(mode="RL")
    # raw_obs = env.get_observation()
    # print("Raw Observation:", raw_obs)
    # processed_obs = env.process_observation(raw_obs)
    # print("Processed Observation:", processed_obs)

    env = GalacticGuardianEnv(mode="RL")

    num_episodes = 3
    action_space_n = 6  # actions 0..5 based on your gg_game.act()

    for ep in range(num_episodes):
        obs, info = env.reset()
        assert isinstance(obs, np.ndarray), "obs is not numpy array"
        assert obs.dtype == np.float32, f"obs dtype is {obs.dtype}, expected float32"

        ep_return = 0.0
        ep_len = 0

        terminated = False
        truncated = False

        while not (terminated or truncated):
            action = np.random.randint(action_space_n)

            next_obs, reward, terminated, truncated, info = env.step(action)

            # basic sanity checks
            assert isinstance(next_obs, np.ndarray)
            assert next_obs.shape == obs.shape, f"obs shape changed: {obs.shape} -> {next_obs.shape}"
            assert np.isfinite(reward), f"non-finite reward: {reward}"

            ep_return += float(reward)
            ep_len += 1
            obs = next_obs

        # pull final raw state for debugging
        final_raw = env.get_observation()
        print(
            f"Episode {ep+1}: len={ep_len}, return={ep_return:.2f}, "
            f"terminated={terminated}, truncated={truncated}, "
            f"final_score={final_raw['score']}, lives={final_raw['remaining_lives']}, level={final_raw['curr_level']}"
        )
        print(env.process_observation(final_raw)[:10])
