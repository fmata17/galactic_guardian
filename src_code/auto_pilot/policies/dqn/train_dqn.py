from __future__ import annotations
import os
import sys
import time
import numpy as np
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
# use comet_ml for experiment tracking and model logging
from comet_ml import Experiment
from comet_ml.integration.pytorch import log_model, watch
import torch

from src_code.auto_pilot.gg_env import GalacticGuardianEnv
from src_code.auto_pilot.policies.dqn.dqn_agent import DQNAgent, DQNConfig
from src_code.auto_pilot.policies.dqn.replay_buffer import ReplayBuffer


def train(
    *,
    mode: str = "stable",  # "minimal" or "stable"
    total_env_steps: int = 200_000,
    replay_size: int = 100_000,
    batch_size: int = 64,
    start_learning_after: int = 5_000,
    train_every: int = 1,
    seed: int = 0,
    device: str = "cpu",
    # for quick overrides without changing DQNConfig
    dqn_override_params: dict | None = None,
    # specify a custom model name for saving the checkpoint
    model_name: str | None = None,
):
    np.random.seed(seed)  # seed RNGs for reproducibility
    torch.manual_seed(seed)

    # load environment variables from .env
    # override=True to ensure we get the latest values from .env, especially for API keys
    if not load_dotenv(find_dotenv(), override=True):
        raise FileNotFoundError(
            "Could not find .env file. Please create one with the necessary environment variables."
        )

    # define the comet_ml experiment
    # API key and workspace are set as environment variables in terminal
    # experiment = start(
    #     api_key=os.getenv("COMET_API_KEY"),
    #     workspace=os.getenv("COMET_WORKSPACE"),
    #     project_name=os.getenv("COMET_PROJECT_NAME", "galactic-guardian")
    # )
    experiment = Experiment(
        api_key=os.getenv("COMET_API_KEY"),
        workspace=os.getenv("COMET_WORKSPACE"),
        project_name=os.getenv("COMET_PROJECT_NAME", "galactic-guardian"),
        auto_param_logging=False,
        auto_metric_logging=False,
        auto_output_logging=False)  # type: ignore

    env = GalacticGuardianEnv(mode="RL")  # create environment instance
    obs, info = env.reset()  # get initial observation and info from environment reset
    obs_dim = int(obs.shape[0])
    # get size of action space predefined in the env
    n_actions = len(env.action_space)

    assert obs_dim == 128, f"Expected obs_dim=128, got {obs_dim}"

    # Create a buffer to store env transitions from initial experience collection,
    #   which will be used for training the DQN agent.
    rb = ReplayBuffer(capacity=replay_size, obs_dim=obs_dim)

    # Specify DQN configuration and create the agent instance.
    cfg = DQNConfig(
        obs_dim=obs_dim,
        n_actions=n_actions,
        gamma=0.99,
        lr=1e-4,
        eps_start=1.0,
        eps_end=0.05,
        eps_decay_steps=150_000,
        mode=mode,
        double_dqn=True,
        target_update_every=1_000,
        grad_clip_norm=10.0,
        device=device,
    )
    if dqn_override_params:
        for key, value in dqn_override_params.items():
            setattr(cfg, key, value)
    agent = DQNAgent(cfg)
    # log the Q-network architecture and gradients to comet_ml during training
    watch(agent.q_net)
    # log the model graph to comet_ml
    experiment.set_model_graph(str(agent.q_net))

    # log the DQN configuration parameters to comet_ml before training starts
    experiment.log_parameters(cfg.__dict__)
    experiment.log_parameters({
        "total_env_steps": total_env_steps,
        "replay_size": replay_size,
        "batch_size": batch_size,
        "start_learning_after": start_learning_after,
        "train_every": train_every,
        "seed": seed,
    })

    # log the environment code defining the reward function to comet_ml for reproducibility and debugging
    env_file_path = sys.modules[GalacticGuardianEnv.__module__].__file__

    if env_file_path:
        experiment.log_code(file_name=env_file_path)

    ep_return = 0.0
    ep_len = 0
    episode = 0
    losses = []  # track losses
    t0 = time.time()

    for global_step in range(1, total_env_steps + 1):
        action = agent.select_action(obs, global_step)

        next_obs, reward, terminated, truncated, info = env.step(action)
        done = bool(terminated or truncated)

        # add experience to replay buffer for training the DQN agent after collecting enough initial experience
        rb.add(obs, action, reward, next_obs, done)

        obs = next_obs
        ep_return += float(reward)
        ep_len += 1

        # learn
        if global_step >= start_learning_after and (global_step % train_every == 0) and len(rb) >= batch_size:
            batch = rb.sample(batch_size)
            logs = agent.train_step(batch)
            losses.append(logs["loss"])

        # log training metrics (not too frequently)
            if global_step % 200 == 0:
                experiment.log_metric("loss", logs["loss"], step=global_step)
                experiment.log_metric(
                    "q_mean", logs["q_mean"], step=global_step)

        if global_step % 500 == 0:
            experiment.log_metric("epsilon", agent.epsilon(
                global_step), step=global_step)
            experiment.log_metric("replay_size", len(rb), step=global_step)

        if done:
            episode += 1
            # grab raw for debugging (score/lives)
            final_raw = env.get_observation()
            # compute average loss over last 100 training steps for logging
            avg_loss = float(np.mean(losses[-100:])) if losses else 0.0

            elapsed = time.time() - t0
            sps = global_step / max(elapsed, 1e-9)  # steps per second

            # log episodic metrics
            experiment.log_metric("avg_loss_100", avg_loss, step=global_step)
            experiment.log_metric("episode_length", ep_len, step=global_step)
            experiment.log_metric(
                "episode_return", ep_return, step=global_step)
            experiment.log_metric(
                "level", final_raw["curr_level"], step=global_step)
            experiment.log_metric(
                "lives", final_raw["remaining_lives"], step=global_step)
            experiment.log_metric(
                "score", final_raw["score"], step=global_step)
            experiment.log_metric("steps_per_sec", sps, step=global_step)

            print(
                f"ep={episode:04d}\t\tstep={global_step:07d} "
                f"episode length={ep_len:4d}\t\tepisode return={ep_return:8.2f} "
                f"term={terminated}\t\ttrunc={truncated} "
                f"score={final_raw['score']}\t\tlives={final_raw['remaining_lives']}\t\tlevel={final_raw['curr_level']} "
                f"epsilon={agent.epsilon(global_step):.3f}\t\tavg_loss_100={avg_loss:.4f}\t\tsteps_per_sec={sps:.1f}"
            )

            # reset environment and episode variables for next episode
            obs, info = env.reset()
            ep_return = 0.0
            ep_len = 0

    # Save checkpoint
    time_stamp = time.strftime("%Y_%m_%d__%H_%M_%S")
    model_name = f"dqn_{mode}_final_{time_stamp}.pt" if not model_name else model_name
    path = Path(__file__).resolve().parent / "trained_models" / model_name
    path.parent.mkdir(parents=True, exist_ok=True)

    # Save final model locally
    agent.save(path.as_posix())

    # Log the raw torch module as a model under the respective directory in comet_ml
    log_model(experiment, agent.q_net, model_name=model_name)

    print(f"Saved: {path}")
    experiment.end()  # end the comet_ml experiment


if __name__ == "__main__":
    # Switch mode between "minimal" and "stable"
    train(
        mode="stable",
        total_env_steps=20_000,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
