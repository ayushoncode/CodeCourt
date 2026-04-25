"""
Baseline script — establishes pre-training metrics.
Run this BEFORE training to get the "before" numbers for your README.

Usage:
    python scripts/baseline.py --episodes 50
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.codecourt_env import CodeCourtEnv
from agents.setter import SetterAgent
from agents.solver import SolverAgent


def update_root_manifest(baseline_payload: dict):
    manifest_path = Path("./outputs/artifact_manifest.json")
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except json.JSONDecodeError:
            manifest = {}
    manifest["baseline"] = baseline_payload
    manifest_path.write_text(json.dumps(manifest, indent=2))


def run_baseline(n_episodes: int = 50, use_brute_force: bool = True):
    """
    Run baseline with:
    - Setter: reference solutions (optimal)
    - Solver: brute-force solutions (suboptimal, will TLE on hard problems)
    """
    env = CodeCourtEnv(difficulty_progression=False)
    setter = SetterAgent(use_reference=True)
    solver = SolverAgent(use_brute_force=use_brute_force)

    results = []
    print(f"\nRunning baseline ({n_episodes} episodes, brute_force={use_brute_force})...")
    print("-" * 60)

    for ep in range(n_episodes):
        obs = env.reset()
        full_problem = env._current_state.problem

        setter_code = setter.generate_solution(full_problem)
        solver_code = solver.solve(full_problem)

        setter_info, solver_info, done, info = env.step(setter_code, solver_code)

        results.append({
            "episode": ep,
            "archetype": obs["archetype"],
            "outcome": info["outcome"],
            "setter_reward": setter_info["reward"],
            "solver_reward": solver_info["reward"],
            "solver_pass_rate": info["solver_pass_rate"],
        })

    # Summary stats
    outcomes = [r["outcome"] for r in results]
    solver_pass_rates = [r["solver_pass_rate"] for r in results]
    solver_rewards = [r["solver_reward"] for r in results]

    summary = {
        "total_episodes": n_episodes,
        "solver_mode": "brute_force" if use_brute_force else "reference",
        "solver_win_rate": outcomes.count("solver_wins") / n_episodes,
        "setter_win_rate": outcomes.count("setter_wins") / n_episodes,
        "invalid_rate": outcomes.count("invalid") / n_episodes,
        "avg_solver_pass_rate": sum(solver_pass_rates) / len(solver_pass_rates),
        "avg_solver_reward": sum(solver_rewards) / len(solver_rewards),
    }

    print(f"\nBaseline Results:")
    print(json.dumps(summary, indent=2))

    # Save
    os.makedirs("./outputs", exist_ok=True)
    with open("./outputs/baseline_results.json", "w") as f:
        json.dump({"summary": summary, "episodes": results}, f, indent=2)
    update_root_manifest({
        "path": "./outputs/baseline_results.json",
        "summary": summary,
    })

    print("\n✓ Baseline saved to ./outputs/baseline_results.json")
    return summary


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=50)
    p.add_argument("--optimal", action="store_true",
                   help="Use optimal solver (sanity check)")
    args = p.parse_args()

    run_baseline(args.episodes, use_brute_force=not args.optimal)
