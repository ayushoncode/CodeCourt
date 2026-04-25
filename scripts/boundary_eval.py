"""
Boundary-condition capability probe for CodeCourt.

This script compares a weak baseline solver against a stronger solver on a
curated suite of small, adversarial, and boundary-heavy cases. The goal is to
produce one crisp artifact that answers: did the solver actually get better at
handling tricky edge conditions?
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.prompts import BRUTE_FORCE_SOLUTIONS, REFERENCE_SOLUTIONS
from oracle.executor import OracleExecutor


CASES = [
    {
        "case_id": "graph_shortest_path_single_node",
        "capability": "boundary_conditions",
        "archetype": "graph",
        "task_id": 0,
        "description": "Shortest-path solver must handle the smallest graph where source equals destination.",
        "input": "1 0\n",
        "expected": "0",
    },
    {
        "case_id": "graph_shortest_path_two_hop",
        "capability": "boundary_conditions",
        "archetype": "graph",
        "task_id": 0,
        "description": "Shortest-path solver must reason beyond direct neighbors.",
        "input": "3 2\n1 2 4\n2 3 5\n",
        "expected": "9",
    },
    {
        "case_id": "graph_bipartite_min_odd_cycle",
        "capability": "boundary_conditions",
        "archetype": "graph",
        "task_id": 1,
        "description": "Bipartite check must reject the smallest odd cycle.",
        "input": "3 3\n1 2\n2 3\n1 3\n",
        "expected": "NO",
    },
    {
        "case_id": "array_lis_hidden_valley",
        "capability": "boundary_conditions",
        "archetype": "array",
        "task_id": 2,
        "description": "LIS must recover after an early overshoot instead of greedily locking in.",
        "input": "4\n2 5 3 4\n",
        "expected": "3",
    },
    {
        "case_id": "dp_lcs_order_sensitive",
        "capability": "boundary_conditions",
        "archetype": "dp",
        "task_id": 2,
        "description": "LCS must respect order, not just character overlap.",
        "input": "abc\nca\n",
        "expected": "1",
    },
    {
        "case_id": "dp_lcs_repeated_chars",
        "capability": "boundary_conditions",
        "archetype": "dp",
        "task_id": 2,
        "description": "LCS must count a subsequence rather than raw character membership.",
        "input": "abc\nac\n",
        "expected": "2",
    },
]


def solver_code(mode: str, archetype: str, task_id: int) -> str:
    key = (archetype, task_id)
    if mode == "brute_force":
        return BRUTE_FORCE_SOLUTIONS.get(key, "print(0)")
    if mode == "reference":
        return REFERENCE_SOLUTIONS.get(key, "print(0)")
    raise ValueError(f"Unsupported mode: {mode}")


def run_suite(mode: str, time_limit: float, memory_limit_mb: int) -> dict:
    executor = OracleExecutor(time_limit=time_limit, memory_limit_mb=memory_limit_mb)
    results = []

    for case in CASES:
        code = solver_code(mode, case["archetype"], case["task_id"])
        result = executor.run(
            code=code,
            stdin_input=case["input"],
            expected_output=case["expected"],
        )
        results.append({
            "case_id": case["case_id"],
            "capability": case["capability"],
            "archetype": case["archetype"],
            "task_id": case["task_id"],
            "description": case["description"],
            "passed": result.passed,
            "status": result.status,
            "outcome": result.outcome,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "expected_output": case["expected"],
            "execution_time": result.execution_time,
        })

    passed = sum(1 for item in results if item["passed"])
    return {
        "mode": mode,
        "total_cases": len(results),
        "passed_cases": passed,
        "pass_rate": passed / max(len(results), 1),
        "cases": results,
    }


def build_summary(baseline: dict, trained: dict) -> dict:
    baseline_map = {case["case_id"]: case for case in baseline["cases"]}
    trained_map = {case["case_id"]: case for case in trained["cases"]}
    improved_cases = []

    for case in CASES:
        case_id = case["case_id"]
        before = baseline_map[case_id]
        after = trained_map[case_id]
        if not before["passed"] and after["passed"]:
            improved_cases.append({
                "case_id": case_id,
                "description": case["description"],
                "archetype": case["archetype"],
                "task_id": case["task_id"],
            })

    return {
        "suite_name": "boundary_conditions",
        "claim": "The solver improves on small, adversarial boundary cases that break shortcut reasoning.",
        "baseline_mode": baseline["mode"],
        "trained_mode": trained["mode"],
        "baseline_pass_rate": baseline["pass_rate"],
        "trained_pass_rate": trained["pass_rate"],
        "pass_rate_delta": trained["pass_rate"] - baseline["pass_rate"],
        "baseline_passed_cases": baseline["passed_cases"],
        "trained_passed_cases": trained["passed_cases"],
        "improved_case_count": len(improved_cases),
        "improved_cases": improved_cases,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Run the CodeCourt boundary-condition capability probe")
    parser.add_argument("--baseline-mode", default="brute_force", choices=["brute_force", "reference"])
    parser.add_argument("--trained-mode", default="reference", choices=["brute_force", "reference"])
    parser.add_argument("--time-limit", type=float, default=2.0)
    parser.add_argument("--memory-limit-mb", type=int, default=256)
    parser.add_argument("--output", default="./outputs/capability_boundary_eval.json")
    return parser.parse_args()


def main():
    args = parse_args()
    baseline = run_suite(args.baseline_mode, args.time_limit, args.memory_limit_mb)
    trained = run_suite(args.trained_mode, args.time_limit, args.memory_limit_mb)
    summary = build_summary(baseline, trained)

    payload = {
        "summary": summary,
        "baseline": baseline,
        "trained": trained,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"Saved boundary probe to {output_path}")


if __name__ == "__main__":
    main()
