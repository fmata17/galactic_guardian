import time
from itertools import product
from src_code.auto_pilot.policies.dqn.train_dqn import train
import torch


def main():
    time_stamp = time.strftime("%Y_%m_%d__%H_%M_%S")

    total_env_steps = 500_000
    replay_size = 200_000

    # Hyperparameters to sweep over
    # Training parameters
    batch_sizes = [64, 128]
    start_learning_afters = [5_000]  # , 10_000

    # DQN config overrides
    lrs = [1e-4, 5e-5]
    # gammas = [0.99, 0.995]
    hidden_sizes = [(256, 256)]  # (128, 128), (128, 128, 128)
    eps_decay_steps = [50_000, 100_000, 200_000]
    target_update_everys = [1_000]  # [500, 1_000, 2_000]
    # grad_clip_norms = [5.0, 10.0]

    run_id = 0

    total_combinations = (len(batch_sizes) * len(start_learning_afters) * len(target_update_everys)
                          # * len(gammas) * len(grad_clip_norms))
                          * len(lrs) * len(hidden_sizes) * len(eps_decay_steps))
    print(f"{"="*50}")
    print(f"Starting DQN hyperparameter sweep")
    print(f"Total hyperparameter combinations to run: {total_combinations}")
    print(
        f"Estimated time: {total_combinations * 45:.2f} minutes or {(total_combinations * 45) / 60:.2f} hours")
    print(f"{"="*50}\n")

    # Sweep over all combinations of hyperparameters and train a DQN agent for each configuration.
    for (batch_size,
         start_learning_after,
         lr,
         #  gamma,
         hidden_size,
         eps_decay_step,
         target_update_every) in product(
        #  grad_clip_norm)
            batch_sizes,
            start_learning_afters,
            lrs,
            # gammas,
            hidden_sizes,
            eps_decay_steps,
            target_update_everys):
        # grad_clip_norms):

        run_id += 1
        print(f"\n{"="*50}\n\tStarting run {run_id} with config:\n"
              f"batch_size={batch_size}\t\tstart_learning_after={start_learning_after}\n"
              # \t\tgamma={gamma}\n"
              f"target_update_every={target_update_every}\t\tlr={lr}\n"
              f"hidden_sizes={hidden_size}\t\teps_decay_steps={eps_decay_step}\n")
        #   f"grad_clip_norm={grad_clip_norm}\n{"="*50}\n")

        # Create a dict of DQN parameters to override the defaults in DQNConfig for this run.
        dqn_override_params = dict(
            lr=lr,
            # gamma=gamma,
            hidden_sizes=hidden_size,
            eps_decay_steps=eps_decay_step,
            target_update_every=target_update_every,
            # grad_clip_norm=grad_clip_norm,
        )

        model_name = f"dqn_stable_sweep_{run_id}_@_{time_stamp}.pt"

        try:
            # Train the DQN agent with the specified configuration.
            train(
                mode="stable",
                total_env_steps=total_env_steps,
                replay_size=replay_size,
                batch_size=batch_size,
                start_learning_after=start_learning_after,
                train_every=1,
                seed=0,
                device="cuda" if torch.cuda.is_available() else "cpu",
                dqn_override_params=dqn_override_params,
                model_name=model_name,
            )
        except Exception as e:
            print(f"Error during run {run_id} with config: "
                  f"batch_size={batch_size}, start_learning_after={start_learning_after}, "
                  # , gamma={gamma}, "
                  f"target_update_every={target_update_every}, lr={lr}"
                  f"hidden_sizes={hidden_size}, eps_decay_steps={eps_decay_step}. Error: {e}")
            #   f"grad_clip_norm={grad_clip_norm}. Error: {e}")
            continue


if __name__ == "__main__":
    main()
