"""
Dynamic problem + trap generation for CodeCourt.

This module keeps the underlying task families executable and oracle-checkable,
while varying the problem flavor, seeded test cases, and post-submission hidden
traps every episode.
"""

from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List

from agents.prompts import BRUTE_FORCE_SOLUTIONS, REFERENCE_SOLUTIONS
from env.problem_types import ARCHETYPES, _format_case, build_problem


TITLE_VARIANTS = {
    ("array", 0): ["Volatility Window", "Signal Recovery", "Profit Shock Segment"],
    ("array", 1): ["Twin Sum Locator", "Checkpoint Pair", "Target Pair Audit"],
    ("array", 2): ["Ascending Chain", "Signal Ladder", "Recovery Sequence"],
    ("graph", 0): ["Critical Route", "Escape Path", "Relay Distance"],
    ("graph", 1): ["Parity Audit", "Two-Color Check", "Odd Cycle Alert"],
    ("graph", 2): ["Cluster Count", "Network Fragments", "Island Detector"],
    ("dp", 0): ["Coin Budget", "Token Minimum", "Change Optimizer"],
    ("dp", 1): ["Stair Sprint", "Climb Counter", "Landing Paths"],
    ("dp", 2): ["Sequence Overlap", "Common Trace", "Alignment Length"],
}

SCENARIO_VARIANTS = {
    "array": [
        "The judge uses hidden stress inputs that punish shortcut reasoning.",
        "Some hidden cases are built to expose greedy mistakes and boundary bugs.",
        "Large adversarial inputs are included to reject inefficient approaches.",
    ],
    "graph": [
        "Disconnected structures and tiny boundary graphs may appear in hidden tests.",
        "The hidden suite includes topology edge cases rather than only random graphs.",
        "Some cases are designed so a local-choice heuristic fails badly.",
    ],
    "dp": [
        "The hidden suite includes small corner cases and order-sensitive cases.",
        "Naive recursion or shortcut pattern matching is intentionally unsafe here.",
        "Boundary values and repeated-symbol cases appear in the hidden evaluation.",
    ],
}

TRAP_EXPLANATIONS = {
    ("array", 0): "Catches brute-force max-subarray scans and incorrect handling of all-negative arrays.",
    ("array", 1): "Catches pair-search logic that mishandles duplicates or only checks one greedy match.",
    ("array", 2): "Catches greedy LIS implementations that lock too early and fail on valley patterns.",
    ("graph", 0): "Catches shortest-path solvers that only inspect direct edges or miss single-node boundaries.",
    ("graph", 1): "Catches bipartite checks that ignore odd cycles or disconnected components.",
    ("graph", 2): "Catches connected-component counters that forget isolated nodes.",
    ("dp", 0): "Catches coin solvers that mishandle zero amount or rely on fragile recursion shortcuts.",
    ("dp", 1): "Catches staircase counters that mishandle n=0 or small boundaries.",
    ("dp", 2): "Catches LCS shortcuts that count overlap instead of preserving order.",
}


def _dedupe_cases(cases: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[Dict[str, str]] = []
    for case in cases:
        key = (case.get("input", ""), case.get("expected", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(case)
    return deduped


def _build_dynamic_case(archetype: str, task_id: int, difficulty: int, rng: random.Random) -> Dict[str, str]:
    if archetype == "array" and task_id == 0:
        if rng.random() < 0.5:
            arr = [-(difficulty + 2), difficulty * 7, -(difficulty + 1), difficulty * 5, -2]
        else:
            arr = [-(difficulty + i + 1) for i in range(max(3, difficulty + 2))]
        return _format_case(archetype, task_id, {"arr": arr})

    if archetype == "array" and task_id == 1:
        arr = [difficulty + 2, difficulty + 2, difficulty * 4 + 1, difficulty * 5 + 3]
        rng.shuffle(arr)
        return _format_case(archetype, task_id, {"arr": arr, "target": (difficulty + 2) * 2})

    if archetype == "array" and task_id == 2:
        arr = [9, 1, 2, 3, 0, 4, 5][: max(5, min(7, 4 + difficulty))]
        return _format_case(archetype, task_id, {"arr": arr})

    if archetype == "graph" and task_id == 0:
        if rng.random() < 0.5:
            return _format_case(archetype, task_id, {"n": 1, "edges": []})
        edges = [(1, 2, 4), (2, 3, 5), (1, 3, 20)]
        return _format_case(archetype, task_id, {"n": 3, "edges": edges})

    if archetype == "graph" and task_id == 1:
        return _format_case(archetype, task_id, {"n": 3, "edges": [(1, 2), (2, 3), (3, 1)]})

    if archetype == "graph" and task_id == 2:
        n = max(4, difficulty * 3 + 1)
        return _format_case(archetype, task_id, {"n": n, "edges": [(1, 2)]})

    if archetype == "dp" and task_id == 0:
        return _format_case(archetype, task_id, {"amount": 0, "coins": [1, 2, 5, 10]})

    if archetype == "dp" and task_id == 1:
        return _format_case(archetype, task_id, {"n": rng.choice([0, 1, 2, 5 + difficulty])})

    if archetype == "dp" and task_id == 2:
        a, b = ("abc", "cba") if rng.random() < 0.5 else ("aaaa", "aa")
        return _format_case(archetype, task_id, {"a": a, "b": b})

    raise ValueError(f"Unsupported dynamic case for {archetype}/{task_id}")


def build_dynamic_problem(archetype: str, task_id: int, difficulty: int, seed: int | None = None) -> Dict[str, Any]:
    """Build a seeded dynamic problem on top of the canonical task family."""
    problem = build_problem(archetype, task_id, difficulty, seed=seed)
    rng = random.Random((seed or 42) + 911)

    dynamic_cases = [_build_dynamic_case(archetype, task_id, difficulty, rng) for _ in range(2)]
    test_cases = _dedupe_cases(list(problem["test_cases"]) + dynamic_cases)
    public_count = min(2, len(test_cases))
    public_test_cases = test_cases[:public_count]
    hidden_test_cases = test_cases[public_count:] or test_cases[-1:]

    title_variant = rng.choice(TITLE_VARIANTS[(archetype, task_id)])
    scenario_note = rng.choice(SCENARIO_VARIANTS[archetype])
    task_name = ARCHETYPES[archetype]["tasks"][task_id]

    problem.update({
        "title": f"{title_variant} [{seed}]",
        "description": (
            f"{problem['description']}\n\n"
            f"Dynamic episode variant: {title_variant.lower()}.\n"
            f"{scenario_note}"
        ),
        "constraints": f"{problem['constraints']} · dynamic seed={seed}",
        "test_cases": test_cases,
        "public_test_cases": public_test_cases,
        "hidden_test_cases": hidden_test_cases,
        "generation_mode": "dynamic",
        "problem_family": task_name,
        "trap_explanation": TRAP_EXPLANATIONS[(archetype, task_id)],
        "reference_solution": REFERENCE_SOLUTIONS.get((archetype, task_id)),
        "brute_force_solution": BRUTE_FORCE_SOLUTIONS.get((archetype, task_id)),
    })
    return problem


def _looks_bruteforce(code: str) -> bool:
    lower = code.lower()
    return (
        "sum(arr[i:j+1])" in lower
        or lower.count("for ") >= 2
        or "while " in lower and "heapq" not in lower and "deque" not in lower
    )


def _trap_candidates(problem: Dict[str, Any], solver_code: str) -> List[Dict[str, str]]:
    archetype = problem["archetype"]
    task_id = problem["task_id"]
    difficulty = max(1, int(problem.get("difficulty", 1)))
    rng = random.Random((problem.get("variant_seed") or 42) + len(solver_code) * 17 + 1337)
    aggressive = _looks_bruteforce(solver_code)

    candidates: list[tuple[dict[str, str], str]] = []

    def add(payload: dict[str, Any], why: str):
        case = _format_case(archetype, task_id, payload)
        candidates.append((case, why))

    if archetype == "array" and task_id == 0:
        add({"arr": [-(difficulty + 3)]}, "Single-element negative array catches bad initialization.")
        arr = [1] * (150 if aggressive else 30)
        arr[len(arr) // 2] = -200
        add({"arr": arr}, "Long adversarial segment punishes quadratic subarray scans.")
    elif archetype == "array" and task_id == 1:
        add({"arr": [4, 4, 7, 9], "target": 8}, "Duplicate-value pair catches solvers that forbid equal numbers at different indices.")
        add({"arr": [2, 11, 7, 15, 9], "target": 18}, "Late valid pair breaks first-match heuristics.")
    elif archetype == "array" and task_id == 2:
        add({"arr": [8, 1, 2, 3, 0, 4, 5]}, "Valley pattern breaks greedy LIS growth.")
        add({"arr": [5, 5, 5, 5, 6]}, "Duplicates expose strict-vs-nonstrict mistakes.")
    elif archetype == "graph" and task_id == 0:
        add({"n": 1, "edges": []}, "Source equals destination catches missing single-node handling.")
        add({"n": 3, "edges": [(1, 2, 4), (2, 3, 5), (1, 3, 20)]}, "Indirect shortest path breaks direct-edge shortcuts.")
    elif archetype == "graph" and task_id == 1:
        add({"n": 3, "edges": [(1, 2), (2, 3), (3, 1)]}, "Minimum odd cycle breaks degree-based or local heuristics.")
        add({"n": 5, "edges": [(1, 2), (3, 4), (4, 5), (5, 3)]}, "Disconnected odd cycle catches partial traversal.")
    elif archetype == "graph" and task_id == 2:
        add({"n": 5, "edges": [(1, 2)]}, "Isolated nodes break component counts based only on seen endpoints.")
        add({"n": 6, "edges": [(1, 2), (2, 3), (4, 5)]}, "Separated clusters plus isolated node catch undercounting.")
    elif archetype == "dp" and task_id == 0:
        add({"amount": 0, "coins": [1, 2, 5, 10]}, "Zero amount catches missing base-case handling.")
        add({"amount": 37 if aggressive else 11, "coins": [1, 2, 5, 10]}, "Larger amount stresses fragile recursion.")
    elif archetype == "dp" and task_id == 1:
        add({"n": 0}, "Zero-step staircase catches off-by-one base cases.")
        add({"n": 1}, "Single-step staircase catches minimal boundary handling.")
    elif archetype == "dp" and task_id == 2:
        add({"a": "abc", "b": "cba"}, "Reversed order catches character-overlap shortcuts.")
        add({"a": "aaaa", "b": "aa"}, "Repeated characters catch incorrect subsequence counting.")

    existing_inputs = {case.get("input", "") for case in problem.get("public_test_cases", []) + problem.get("hidden_test_cases", [])}
    traps: list[Dict[str, str]] = []
    for case, why in candidates:
        if case["input"] in existing_inputs:
            continue
        trap = dict(case)
        trap["why_it_breaks"] = why
        traps.append(trap)
        existing_inputs.add(case["input"])

    rng.shuffle(traps)
    return traps[:2]


def generate_dynamic_trap_tests(problem: Dict[str, Any], solver_code: str) -> List[Dict[str, str]]:
    """Generate up to two fresh hidden tests targeted at the current solver submission."""
    if not solver_code.strip():
        return []
    traps = _trap_candidates(problem, solver_code)
    if traps:
        return traps

    archetype = problem["archetype"]
    task_id = problem["task_id"]
    seed = int(problem.get("variant_seed") or 42)
    difficulty = max(1, int(problem.get("difficulty", 1)))
    existing_inputs = {case.get("input", "") for case in problem.get("public_test_cases", []) + problem.get("hidden_test_cases", [])}

    fallback_payloads = {
        ("array", 0): {"arr": [seed % 7 - 12, seed % 5 + 3, -20, seed % 11 + 9]},
        ("array", 1): {"arr": [3, 8, 3, 11, 14], "target": 6},
        ("array", 2): {"arr": [10, 1, 9, 2, 8, 3, 4]},
        ("graph", 0): {"n": 4, "edges": [(1, 2, 2), (2, 4, 2), (1, 4, 10), (2, 3, 1), (3, 4, 1)]},
        ("graph", 1): {"n": 6, "edges": [(1, 2), (2, 3), (3, 1), (4, 5)]},
        ("graph", 2): {"n": 7, "edges": [(1, 2), (2, 3), (4, 5)]},
        ("dp", 0): {"amount": difficulty * 23 + (seed % 5), "coins": [1, 2, 5, 10]},
        ("dp", 1): {"n": difficulty * 8 + (seed % 4)},
        ("dp", 2): {"a": "abca" + ("b" * (seed % 3)), "b": "caba"},
    }

    case = _format_case(archetype, task_id, fallback_payloads[(archetype, task_id)])
    if case["input"] in existing_inputs:
        return []
    case["why_it_breaks"] = "Fresh fallback trap generated from the episode seed to force a new hidden check."
    return [case]
