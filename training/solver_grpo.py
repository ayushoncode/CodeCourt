"""
Utilities for training the solver with TRL GRPO.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from agents.prompts import SOLVER_SYSTEM, SOLVER_USER_TEMPLATE
from env.problem_types import ARCHETYPES, build_problem
from oracle.executor import OracleExecutor


CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class SolverTrainingSample:
    prompt: str
    test_cases_json: str
    optimal_complexity: str
    archetype: str
    task_id: int
    difficulty: int


def build_solver_prompt(problem: dict[str, Any]) -> str:
    return SOLVER_SYSTEM + "\n\n" + SOLVER_USER_TEMPLATE.format(
        description=problem["description"]
    )


def make_solver_dataset(num_samples: int, max_difficulty: int = 3) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    archetype_names = list(ARCHETYPES.keys())

    sample_id = 0
    while len(samples) < num_samples:
        for difficulty in range(1, max_difficulty + 1):
            for archetype in archetype_names:
                tasks = ARCHETYPES[archetype]["tasks"]
                for task_id in range(len(tasks)):
                    seed = 1000 + sample_id * 17 + difficulty * 101 + task_id * 13
                    problem = build_problem(archetype, task_id, difficulty, seed=seed)
                    sample = SolverTrainingSample(
                        prompt=build_solver_prompt(problem),
                        test_cases_json=json.dumps(problem["test_cases"]),
                        optimal_complexity=problem.get("optimal_complexity", "O(N)"),
                        archetype=archetype,
                        task_id=task_id,
                        difficulty=difficulty,
                    )
                    row = sample.__dict__.copy()
                    row["sample_id"] = sample_id
                    row["variant_seed"] = seed
                    samples.append(row)
                    sample_id += 1
                    if len(samples) >= num_samples:
                        return samples
    return samples


def extract_python_code(text: str) -> str:
    if not text:
        return ""
    match = CODE_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def make_solver_reward_functions(
    time_limit: float,
    memory_limit_mb: int,
):
    from rewards.rubrics import SolverRubric

    oracle = OracleExecutor(time_limit=time_limit, memory_limit_mb=memory_limit_mb)
    rubric = SolverRubric()

    def execution_reward(
        completions,
        test_cases_json,
        optimal_complexity,
        log_extra=None,
        log_metric=None,
        **kwargs,
    ):
        import requests
        import threading
        
        def broadcast_async(payload):
            try:
                requests.post("http://127.0.0.1:7860/api/internal/broadcast", json=payload, timeout=1.0)
            except Exception:
                pass

        rewards: list[float] = []
        pass_rates: list[float] = []
        statuses: list[str] = []

        robustness_scores: list[float] = []

        for completion, raw_tests, complexity in zip(completions, test_cases_json, optimal_complexity):
            code = extract_python_code(completion)
            if not code:
                rewards.append(-25.0)
                pass_rates.append(0.0)
                statuses.append("empty")
                robustness_scores.append(-1.0)
                
                threading.Thread(target=broadcast_async, args=({
                    "code": "Empty submission",
                    "pass_rate": 0.0,
                    "reward": -25.0,
                    "status": "empty",
                    "outcome": "setter_wins"
                },)).start()
                continue

            test_cases = json.loads(raw_tests)
            result = oracle.run_against_tests(code, test_cases)
            breakdown = rubric.score(
                public_result=result,
                hidden_result=result,
                solver_code=code,
                optimal_complexity=complexity,
            )
            reward = float(breakdown.total)
            
            threading.Thread(target=broadcast_async, args=({
                "code": code,
                "pass_rate": float(result["pass_rate"]),
                "reward": reward,
                "status": result["overall_status"],
                "outcome": result["outcome"]
            },)).start()

            rewards.append(float(reward))
            pass_rates.append(float(result["pass_rate"]))
            statuses.append(result["overall_status"])
            robustness_scores.append(float(
                breakdown.components.get("complexity_match", 0.0)
                + breakdown.components.get("fast_io_bonus", 0.0)
                + breakdown.components.get("complexity_risk", 0.0)
            ))

        if log_extra:
            log_extra("solver_status", statuses)
            log_extra("solver_pass_rate", [f"{rate:.2f}" for rate in pass_rates])
        if log_metric and pass_rates:
            log_metric("reward_pass_rate", sum(pass_rates) / len(pass_rates))
            log_metric("reward_robustness", sum(robustness_scores) / len(robustness_scores))

        return rewards

    def format_reward(completions, **kwargs):
        rewards: list[float] = []
        for completion in completions:
            code = extract_python_code(completion)
            if not code:
                rewards.append(-2.0)
                continue

            lines = [line for line in code.splitlines() if line.strip()]
            reward = 0.5
            if any("input(" in line or "sys.stdin" in line for line in lines):
                reward += 0.5
            if "```" in completion:
                reward -= 1.0
            rewards.append(reward)
        return rewards

    return [execution_reward, format_reward]
