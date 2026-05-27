import time
import argparse
from pathlib import Path
from src_code.auto_pilot.gg_env import GalacticGuardianEnv
from src_code.auto_pilot.policies.random_policy import RandomPolicy
from src_code.auto_pilot.policies.nearest_policy import NearestPolicy
from src_code.auto_pilot.policies.dqn_policy import DQNPolicy, DQNPolicyConfig


def _parse_args():
    """Parse command-line arguments for running different policies easily."""
    parser = argparse.ArgumentParser(
        description="Run a policy in the Galactic Guardian environment.")
    parser.add_argument("--policy", type=str, default="random",
                        help="Type of policy to run (default: random)")
    parser.add_argument("--num_episodes", type=int, default=10,
                        help="Number of episodes to run (default: 10)")
    parser.add_argument("--mode", type=str, default="RL", choices=["RL", "human", "manual"],
                        help="Environment mode (default: RL) - can be 'RL', 'human', or 'manual')")
    parser.add_argument("--model_path", type=str, default=None,
                        help="Path to the trained DQN model checkpoint (required if policy=dqn)")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device to run the DQN policy on (default: cpu)")
    return parser.parse_args()


def _get_policy(policy_type: str):
    """Return an instance of the specified policy type."""
    if policy_type == "random":
        return RandomPolicy()
    elif policy_type == "nearest":
        return NearestPolicy()
    elif policy_type == "dqn":
        if not args.model_path:
            raise ValueError("--model_path is required for policy=dqn")
        if args.device != "cuda":
            if input(f"Warning: Running DQN on {args.device} may be slow. Continue? (y/n) ").lower() != "y":
                print("Exiting.")
                exit(0)
        return DQNPolicy(DQNPolicyConfig(model_path=args.model_path, device=args.device))
    else:
        raise ValueError(f"Unknown policy type: '{policy_type}'")


def _logger(run_info, to_file=False, last=False):
    """A simple logger to print and possibly save the observations and run information."""
    # Extract run information
    episode, episodes = run_info["episode"], run_info["episodes"]
    steps = run_info["steps"]
    episode_reward, total_reward = run_info["episode_reward"], run_info["total_reward"]
    run_id = run_info.get("run_id", "N/A")

    message = f"""
{"-" * 100}
Episode: {episode + 1}\t\tEpisode Steps: {steps}\t\tEpisode Reward: {episode_reward}\t\tTotal Reward Accumulated: {total_reward}
{"-" * 100}
""".strip() + "\n" if not last else f"""
{"-" * 65}
Total Reward: {total_reward}\t\tAverage Reward per Episode: {total_reward / episodes}\t\tRun ID: {run_id}
{"-" * 65}
""".strip() + "\n"
    if to_file:  # Optionally save the log to a file
        path = Path(__file__).resolve().parent / "logs" / "runstats.txt"
        path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the logs directory exists
        with open(path, "a") as f:
            f.write(message)
    print(message)


def run_policy(policy, env, num_episodes=10, mode="RL"):
    """Run a given policy in the environment for a specified number of episodes."""
    run_id = time.strftime("%Y%m%d_%H%M%S")
    total_reward = 0
    if hasattr(env.action_space, "n"):
        valid_actions = list(range(env.action_space.n))
    else:
        valid_actions = list(env.action_space)
    action_min, action_max = min(valid_actions), max(valid_actions)
    for episode in range(num_episodes):
        # Reset the environment at the start of each episode
        observation, info = env.reset()
        terminated = False
        truncated = False
        episode_reward = 0
        episode_steps = 0

        # Check if the game window is still open for graceful exit (env.gg_game.running)
        while not terminated and not truncated and env.gg_game.running:
            episode_steps += 1
            if mode == "manual":
                while True:
                    raw_action = input(
                        f"Action id [{action_min}-{action_max}] (or 'q' to quit): ").strip().lower()
                    if raw_action == "q":
                        terminated = True
                        break
                    if raw_action.isdigit() and int(raw_action) in valid_actions:
                        action_id = int(raw_action)
                        break
                    print(
                        f"Invalid action. Enter a number between {action_min} and {action_max}, or 'q'.")
                if terminated:
                    break
            else:
                action_id = policy.select_action(
                    observation)  # Get action from the policy
            next_observation, reward, terminated, truncated, info = env.step(
                action_id)  # Take action in the environment
            episode_reward += reward  # Accumulate reward
            total_reward += reward

            observation = next_observation  # Update observation for the next step
            if mode == "human":
                # Sleep briefly to slow down the loop for better visualization
                time.sleep(0.01)

        # Log episode information after each episode
        run_info = {
            "episode": episode,
            "episodes": num_episodes,
            "steps": episode_steps,
            "episode_reward": episode_reward,
            "total_reward": total_reward
        }
        _logger(run_info, to_file=False, last=False)

    # Log final run information
    run_info = {
        "episode": None,
        "episodes": num_episodes,
        "steps": None,
        "episode_reward": None,
        "total_reward": total_reward,
        "run_id": run_id
    }
    _logger(run_info, to_file=False, last=True)


if __name__ == "__main__":
    args = _parse_args()
    policy = _get_policy(args.policy)
    env = GalacticGuardianEnv(mode=args.mode)
    run_policy(policy, env, num_episodes=args.num_episodes, mode=args.mode)
