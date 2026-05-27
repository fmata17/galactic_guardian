from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from src_code.auto_pilot.policies.dqn.replay_buffer import Batch


class QNetwork(nn.Module):
    """Vanilla MLP for DQN."""

    def __init__(self, obs_dim: int, n_actions: int, hidden_sizes: tuple[int, ...]):
        super().__init__()
        layers = []
        in_dim = obs_dim
        for h in hidden_sizes:
            layers.append(nn.Linear(in_dim, h))
            layers.append(nn.ReLU())
            in_dim = h
        layers.append(nn.Linear(in_dim, n_actions))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@dataclass
class DQNConfig:
    """Configuration for DQN agent."""
    obs_dim: int
    n_actions: int
    hidden_sizes: tuple[int, ...] = (128, 128)
    gamma: float = 0.99
    lr: float = 1e-4

    # exploration
    eps_start: float = 1.0  # full exploration at the start of training
    eps_end: float = 0.05  # mostly exploitation at the end of training
    eps_decay_steps: int = 100_000

    # training
    mode: str = "stable"  # "minimal" or "stable"
    double_dqn: bool = True          # only used in stable mode
    target_update_every: int = 1_000  # only used in stable mode
    grad_clip_norm: float = 10.0     # only used in stable mode

    device: str = "cuda"


class DQNAgent:
    """
    DQN agent with support for both minimal and stable modes to compare results.
    - In "minimal" mode, the agent uses a single Q-network without a target network and trains with MSE loss.
    - In "stable" mode, the agent uses a target network, supports Double DQN, and trains with Huber loss, 
        which are all techniques to improve training stability.
    """

    def __init__(self, cfg: DQNConfig):
        assert cfg.mode in ("minimal", "stable")
        self.cfg = cfg

        self.device = torch.device(cfg.device)

        # Create Q-network and optimizer
        self.q_net = QNetwork(cfg.obs_dim, cfg.n_actions, cfg.hidden_sizes).to(self.device)
        self.optim = torch.optim.Adam(self.q_net.parameters(), lr=cfg.lr)

        # create target network if in stable mode
        self.target_net = None
        if cfg.mode == "stable":
            self.target_net = QNetwork(
                cfg.obs_dim, cfg.n_actions, cfg.hidden_sizes).to(self.device)
            # Initialize target network weights to match those of q_net
            self.target_net.load_state_dict(self.q_net.state_dict())
            # Set target network to eval mode since it's only used for inference
            self.target_net.eval()

        self._train_steps = 0

    def epsilon(self, global_step: int) -> float:
        """
        Linearly decaying epsilon from 1.0 to 0.05 over 100,000 steps to balance exploration and exploitation in
        reinforcement learning, starting with full exploration and shifting towards exploitation as training progresses.
        Other exploration strategies include exponential decay, Boltzmann exploration, and Thompson sampling,
        which can also be used depending on the task requirements.
        """
        # clamp to [0, eps_decay_steps]
        t = min(max(global_step, 0), self.cfg.eps_decay_steps)
        frac = t / self.cfg.eps_decay_steps  # 0.0 at step 0, 1.0 at step eps_decay_steps
        return self.cfg.eps_start + frac * (self.cfg.eps_end - self.cfg.eps_start)

    @torch.no_grad()
    def select_action(self, obs: np.ndarray, global_step: int) -> int:
        """Epsilon-greedy action selection."""
        # First iterations will have higher epsilon for more exploration,
        #   which decays over time to encourage exploitation of learned policy.
        eps = self.epsilon(global_step)
        # At the beginning of training, when the agent has no knowledge, it will take random actions.
        if np.random.rand() < eps:
            return int(np.random.randint(self.cfg.n_actions))

        # (1, obs_dim)
        obs_t = torch.as_tensor(obs, dtype=torch.float32,
                                device=self.device).unsqueeze(0)

        # Get logits for all actions from the Q-network and select the action with the highest Q-value.
        q = self.q_net(obs_t)  # (1, n_actions)
        return int(torch.argmax(q, dim=1).item())

    def maybe_update_target(self):
        """Update target network if in stable mode and it's time to update."""
        if self.cfg.mode != "stable":
            return
        # Update target network every {target_update_every} steps by copying weights from q_net
        if self._train_steps % self.cfg.target_update_every == 0 and self.target_net is not None:
            self.target_net.load_state_dict(self.q_net.state_dict())

    def train_step(self, batch: Batch) -> dict:
        """
        One gradient update from a replay batch.
        Returns logging dict.
        """
        # Get batch data as tensors on the correct device for training the Q-network.
        obs = torch.as_tensor(batch.obs, dtype=torch.float32,
                              # (B, obs_dim)
                              device=self.device)
        actions = torch.as_tensor(
            # (B,)
            batch.actions, dtype=torch.int64, device=self.device)
        rewards = torch.as_tensor(
            # (B,)
            batch.rewards, dtype=torch.float32, device=self.device)
        next_obs = torch.as_tensor(
            # (B, obs_dim)
            batch.next_obs, dtype=torch.float32, device=self.device)
        dones = torch.as_tensor(
            # (B,)
            batch.dones, dtype=torch.float32, device=self.device)

        # Compute current Q-values (logits) for the actions taken in the batch using the Q-network.
        q_values = self.q_net(obs)  # (B, n_actions)
        # Q-values for the actions taken
        q_sa = q_values.gather(1, actions.unsqueeze(1)).squeeze(1)  # (B,)

        with torch.no_grad():
            if self.cfg.mode == "stable" and self.target_net is not None:
                # Target network used
                if self.cfg.double_dqn:
                    # Double DQN: action selection from q_net, evaluation from target_net
                    next_actions = torch.argmax(
                        self.q_net(next_obs), dim=1)  # (B,)
                    next_q = self.target_net(next_obs).gather(
                        1, next_actions.unsqueeze(1)).squeeze(1)
                else:
                    next_q = torch.max(self.target_net(next_obs), dim=1).values
            else:
                # Minimal mode: bootstrap from same network (less stable)
                next_q = torch.max(self.q_net(next_obs), dim=1).values

            # Compute target Q-values using the Bellman update: target = reward + gamma * max_a' Q(next_obs, a')
            target = rewards + self.cfg.gamma * (1.0 - dones) * next_q  # (B,)

        if self.cfg.mode == "stable":
            loss = F.smooth_l1_loss(q_sa, target)  # Huber loss
        else:
            loss = F.mse_loss(q_sa, target)

        self.optim.zero_grad(set_to_none=True)  # zero out gradients
        loss.backward()  # compute gradients of loss w.r.t. Q-network parameters

        if self.cfg.mode == "stable" and self.cfg.grad_clip_norm is not None:
            nn.utils.clip_grad_norm_(
                self.q_net.parameters(), self.cfg.grad_clip_norm)

        self.optim.step()  # backpropagate and update Q-network parameters

        self._train_steps += 1
        # update target network if in stable mode and it's time to update
        self.maybe_update_target()

        return {
            "loss": float(loss.item()),
            "q_mean": float(q_sa.mean().item()),
            "target_mean": float(target.mean().item()),
        }

    def save(self, path: str):
        """
        Save the Q-network (and target network if in stable mode) state dicts
        along with the configuration for later loading.
        """
        payload = {
            "cfg": self.cfg.__dict__,  # save config dict for reference and reproducibility
            "q_net": self.q_net.state_dict(),
        }
        if self.target_net is not None:
            payload["target_net"] = self.target_net.state_dict()
        torch.save(payload, path)

    def load(self, path: str):
        """Load the Q-network (and target network if in stable mode) state dicts from a saved file."""
        payload = torch.load(path, map_location=self.device)
        self.q_net.load_state_dict(payload["q_net"])
        if self.target_net is not None and "target_net" in payload:
            self.target_net.load_state_dict(payload["target_net"])


# debugging purposes
if __name__ == "__main__":

    agent = DQNAgent(DQNConfig(obs_dim=127, n_actions=6, mode="stable"))
    print(agent.q_net)
    print("\n\n")
    print(agent.target_net)
