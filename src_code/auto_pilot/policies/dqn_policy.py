"""
DQNPolicy: load a trained DQN checkpoint (.pt) and select actions from it.

This policy is compatible with run_policy.py that expects:
    action_id = policy.select_action(observation)

Assumptions:
- observation is a numpy array (processed obs) shaped (obs_dim,)
- action space is discrete [0..n_actions-1]
- checkpoint was saved by our DQNAgent.save(), containing:
    {
      "cfg": { "obs_dim": int, "n_actions": int, ... },
      "q_net": <state_dict>,
      ... (optional target_net)
    }
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import torch

# Import the exact network class used during training.
# This is important: DQN checkpoints generally cannot be loaded safely unless
# the architecture matches exactly.
from src_code.auto_pilot.policies.dqn.dqn_agent import QNetwork


@dataclass
class DQNPolicyConfig:
    model_path: str
    device: str = "cpu"          # "cpu" or "cuda"
    # True => greedy argmax; False could do sampling (not typical for DQN)
    deterministic: bool = True
    verbose: bool = False        # Print some info on load


class DQNPolicy:
    """
    A policy wrapper around a trained Q-network.

    - Loads a saved .pt checkpoint
    - Runs a forward pass: Q(s, a) for all actions
    - Returns argmax_a Q(s, a)
    """

    def __init__(self, cfg: DQNPolicyConfig):
        self.cfg = cfg
        self.device = torch.device(cfg.device)

        # Load checkpoint
        ckpt = torch.load(cfg.model_path, map_location=self.device)

        if "cfg" not in ckpt or "q_net" not in ckpt:
            raise ValueError(
                "Checkpoint format not recognized. Expected keys: 'cfg' and 'q_net'. "
                "Tip: print(torch.load(path).keys()) and share it."
            )

        saved_cfg = ckpt["cfg"]
        self.obs_dim = int(saved_cfg["obs_dim"])
        self.n_actions = int(saved_cfg["n_actions"])
        self.hidden_sizes = tuple(saved_cfg.get("hidden_sizes", (128, 128)))

        # Rebuild the network with the same dimensions used during training
        self.q_net = QNetwork(self.obs_dim, self.n_actions,
                              self.hidden_sizes).to(self.device)
        self.q_net.load_state_dict(ckpt["q_net"])
        self.q_net.eval()

        if cfg.verbose:
            print(
                f"[DQNPolicy] Loaded model from '{cfg.model_path}' "
                f"(obs_dim={self.obs_dim}, n_actions={self.n_actions}, hidden_sizes={self.hidden_sizes}, device={self.device})"
            )

    @torch.no_grad()
    def select_action(self, observation: np.ndarray) -> int:
        """
        Compute action from the current observation.

        Parameters
        ----------
        observation : np.ndarray
            Processed observation vector of shape (obs_dim,).

        Returns
        -------
        int
            Action id in [0, n_actions-1].
        """
        # Basic sanity checks (for early integration)
        if not isinstance(observation, np.ndarray):
            observation = np.array(observation, dtype=np.float32)

        if observation.shape[0] != self.obs_dim:
            raise ValueError(
                f"Obs dim mismatch: got {observation.shape[0]}, expected {self.obs_dim}. "
                "Are you using the same env observation layout as training?"
            )

        # Convert to torch tensor and add batch dimension
        obs_t = torch.as_tensor(
            # (1, obs_dim)
            observation, dtype=torch.float32, device=self.device).unsqueeze(0)

        # Forward pass: Q-values for all actions
        q_values = self.q_net(obs_t)  # (1, n_actions)

        # Greedy action selection
        if self.cfg.deterministic:
            action = int(torch.argmax(q_values, dim=1).item())
        else:
            # Implements stochastic action selection if needed
            action_probs = torch.softmax(q_values, dim=1)  # (1, n_actions)
            action = int(torch.multinomial(action_probs, num_samples=1).item())
        return action
