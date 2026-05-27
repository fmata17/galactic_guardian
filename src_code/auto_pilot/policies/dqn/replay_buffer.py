from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class Batch:
    obs: np.ndarray        # (B, obs_dim)   float32
    actions: np.ndarray    # (B,)           int64
    rewards: np.ndarray    # (B,)           float32
    next_obs: np.ndarray   # (B, obs_dim)   float32
    dones: np.ndarray      # (B,)           float32  (1.0 if done else 0.0)


class ReplayBuffer:
    """
    Buffer to store environment transitions after each step,
    and sample random batches after enough data is collected for training the DQN agent.
    Stores observations, actions, rewards, next observations, and done flags
        in separate numpy arrays for efficient indexing and sampling.
    """

    def __init__(self, capacity: int, obs_dim: int):
        self.capacity = int(capacity)
        self.obs_dim = int(obs_dim)

        self._obs = np.zeros((self.capacity, self.obs_dim), dtype=np.float32)
        self._actions = np.zeros((self.capacity,), dtype=np.int64)
        self._rewards = np.zeros((self.capacity,), dtype=np.float32)
        self._next_obs = np.zeros(
            (self.capacity, self.obs_dim), dtype=np.float32)
        self._dones = np.zeros((self.capacity,), dtype=np.float32)

        self._size = 0  # tracks current number of transitions stored
        self._pos = 0  # tracks next position to insert new transition

    def __len__(self) -> int:  # override len() to return current size of buffer
        return self._size

    def add(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool):
        """Add a new transition to the buffer, overwriting old data if capacity is exceeded."""
        i = self._pos
        self._obs[i] = obs
        self._actions[i] = int(action)
        self._rewards[i] = float(reward)
        self._next_obs[i] = next_obs
        self._dones[i] = 1.0 if done else 0.0

        # overwrite old data when capacity is exceeded
        self._pos = (self._pos + 1) % self.capacity
        # track current size up to capacity
        self._size = min(self._size + 1, self.capacity)

    def sample(self, batch_size: int) -> Batch:
        """Randomly sample indices in the range of currently stored transitions to batch the data for training."""
        assert self._size > 0, "Cannot sample from an empty replay buffer."
        idx = np.random.randint(0, self._size, size=batch_size)

        return Batch(
            obs=self._obs[idx],
            actions=self._actions[idx],
            rewards=self._rewards[idx],
            next_obs=self._next_obs[idx],
            dones=self._dones[idx],
        )
