import numpy.random as random


class RandomPolicy:
    """A simple policy that selects actions randomly from the action space."""

    def select_action(self, observation):
        """Select an action randomly from the action space."""
        # The action space defined in the environment
        action_space = [0, 1, 2, 3, 4, 5]
        return random.choice(action_space)
