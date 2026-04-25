"""
Legacy episode runner for CodeCourt.
This keeps the old simulation-only loop available for quick smoke tests.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.setter import SetterAgent
from agents.solver import SolverAgent
from env.codecourt_env import CodeCourtEnv


def parse_args():
    parser = argparse.ArgumentParser(description="Legacy CodeCourt mock runner")
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--save-every", type=int, default=50)
    parser.add_argument("--output-dir", type=str, default="./outputs")
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    setter = SetterAgent(use_reference=True)
    solver = SolverAgent(use_reference=False, use_brute_force=False)
    env = CodeCourtEnv(difficulty_progression=True)

    history = []
    for ep in range(args.episodes):
        obs = env.reset()
        full_problem = env._current_state.problem

        setter_code = setter.generate_solution(full_problem)
        solver_code = solver.solve(full_problem)
        setter_info, solver_info, _, info = env.step(setter_code, solver_code)

        record = {
            "episode": ep,
            "archetype": obs["archetype"],
            "task_id": obs["task_id"],
            "difficulty": obs["difficulty"],
            "setter_reward": setter_info["reward"],
            "solver_reward": solver_info["reward"],
            "outcome": info["outcome"],
            "setter_elo": info["elo"]["setter_elo"],
            "solver_elo": info["elo"]["solver_elo"],
            "solver_pass_rate": info["solver_pass_rate"],
        }
        history.append(record)

        if (ep + 1) % args.save_every == 0:
            ckpt_path = os.path.join(args.output_dir, f"history_ep{ep+1}.json")
            with open(ckpt_path, "w") as f:
                json.dump(history, f, indent=2)

    final_path = os.path.join(args.output_dir, "training_history.json")
    with open(final_path, "w") as f:
        json.dump(history, f, indent=2)

    print(f"Saved legacy mock history to {final_path}")


if __name__ == "__main__":
    main()
