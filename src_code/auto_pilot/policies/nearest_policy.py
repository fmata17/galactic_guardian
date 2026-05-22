class NearestPolicy:
    """
    A simple policy that always moves towards the nearest enemy.
    """

    def _process_observation(self, observation):
        self.ship_center_x_std = observation[1]
        self.ship_center_y_std = observation[2]
        self.ship_width_std = observation[3]
        self.ship_height_std = observation[4]
        # Order is aliens from left to right
        self.aliens_center_x_std = observation[7::4]
        # Order is aliens from up to down
        self.aliens_center_y_std = observation[8::4]
        self.aliens = {i: (k, l) for i, (k, l) in enumerate(
            zip(self.aliens_center_x_std, self.aliens_center_y_std))}

    def _find_nearest_alien(self):
        """
        Find the nearest alien to the ship.
        """
        min_distance = float('inf')
        nearest_alien = None
        for i, (alien_x, alien_y) in self.aliens.items():
            distance = ((self.ship_center_x_std - alien_x) ** 2 +
                        (self.ship_center_y_std - alien_y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_alien = (i, alien_x, alien_y)
        return nearest_alien

    def select_action(self, observation):
        """
        Select an action based on the current state.
        """
        self._process_observation(observation)
        nearest_alien = self._find_nearest_alien()
        if nearest_alien is None:
            return 0  # No aliens, do nothing

        _, alien_x, _ = nearest_alien
        # Simple heuristic logic:
        # if the nearest alien is to the right of the ship, move right and fire; if to the left, move left and fire
        if alien_x > self.ship_center_x_std + self.ship_width_std / 2:
            return 4  # Move right and fire bullet
        elif alien_x < self.ship_center_x_std - self.ship_width_std / 2:
            return 5  # Move left and fire bullet
        else:
            return 3  # Fire bullet
