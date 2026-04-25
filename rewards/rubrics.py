"""
Composable reward rubrics following OpenEnv spec.
Separate rubrics for Setter validity, Solver correctness, efficiency.
"""

import ast
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class RewardBreakdown:
    total: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)
    reason: str = ""

    def add(self, name: str, value: float, reason: str = ""):
        self.components[name] = value
        self.total += value
        if reason:
            self.reason += f" | {name}: {reason}"


class SetterRubric:
    """
    Setter reward rubric.

    Core logic (minimax):
      - Setter earns points if Solver FAILS
      - But ONLY if Setter can solve its own problem (self-consistency gate)
      - Penalty if problem is invalid or Setter can't solve it
    """

    def score(
        self,
        setter_result: Dict,
        solver_public_result: Dict,
        solver_hidden_result: Dict,
        problem_valid: bool,
        optimal_complexity: str = "O(N)",
    ) -> RewardBreakdown:
        rb = RewardBreakdown()

        # Gate: invalid problem
        if not problem_valid:
            rb.add("invalid_problem", -20.0, "Problem failed validation")
            return rb

        # Gate: Setter must be able to solve its own problem
        setter_passed = setter_result.get("overall_status") == "pass"
        if not setter_passed:
            rb.add("setter_cannot_solve", -30.0,
                   "Setter failed its own test cases — problem is invalid")
            return rb

        # Core adversarial reward
        hidden_status = solver_hidden_result.get("overall_status", "fail")
        hidden_pass_rate = solver_hidden_result.get("pass_rate", 0.0)
        public_pass_rate = solver_public_result.get("pass_rate", 0.0)

        if hidden_status == "pass":
            # Solver passed — Setter loses this round
            rb.add("solver_passed", -10.0, "Solver succeeded — Setter loses")

        elif hidden_status == "tle":
            # Solver TLE'd — Setter found a hard problem
            rb.add("solver_tle", +40.0, "Solver TLE — Setter exploited complexity")

        elif hidden_status in ("fail", "error"):
            # Solver wrong answer
            rb.add("solver_wrong", +50.0, "Solver wrong answer — Setter wins")

        if hidden_pass_rate < public_pass_rate:
            rb.add("hidden_test_gap", +10.0, "Hidden tests are meaningfully harder than public tests")

        # Bonus: reward tight pass rate (close to failing but valid)
        pass_rate = setter_result.get("pass_rate", 1.0)
        if pass_rate == 1.0:
            rb.add("clean_solution", +5.0, "Setter has clean reference solution")

        return rb


class SolverRubric:
    """
    Solver reward rubric.

    Rewards correct + efficient solutions.
    Penalizes brute-force TLE harder than wrong answers
    to push toward algorithmic thinking.
    """

    COMPLEXITY_ORDER = ["O(1)", "O(log N)", "O(N)", "O(N log N)",
                        "O(N^2)", "O(N^3)", "O(2^N)"]

    FORBIDDEN_PATTERNS = [
        ("import os", -8.0, "Uses os module"),
        ("import subprocess", -12.0, "Uses subprocess module"),
        ("open(", -8.0, "Reads or writes files"),
        ("exec(", -12.0, "Uses exec"),
        ("eval(", -12.0, "Uses eval"),
        ("socket", -12.0, "Uses networking module"),
        ("requests", -12.0, "Uses requests"),
    ]

    def _complexity_rank(self, complexity: str) -> int:
        for i, c in enumerate(self.COMPLEXITY_ORDER):
            if c.lower() in complexity.lower():
                return i
        return 4  # Default to O(N^2) if unknown

    def _estimate_algorithmic_risk(self, solver_code: str) -> tuple[int, bool, int]:
        try:
            tree = ast.parse(solver_code)
        except SyntaxError:
            return 3, False, 0

        max_loop_depth = 0
        if_count = 0

        def walk(node: ast.AST, depth: int = 0):
            nonlocal max_loop_depth, if_count
            if isinstance(node, (ast.For, ast.While)):
                depth += 1
                max_loop_depth = max(max_loop_depth, depth)
            if isinstance(node, ast.If):
                if_count += 1
            for child in ast.iter_child_nodes(node):
                walk(child, depth)

        walk(tree)
        uses_fast_io = "sys.stdin" in solver_code or "stdin.readline" in solver_code
        return max_loop_depth, uses_fast_io, if_count

    def score(
        self,
        public_result: Dict,
        hidden_result: Dict,
        solver_code: str,
        optimal_complexity: str = "O(N)",
    ) -> RewardBreakdown:
        rb = RewardBreakdown()

        status = hidden_result.get("overall_status", "fail")
        hidden_pass_rate = hidden_result.get("pass_rate", 0.0)
        public_pass_rate = public_result.get("pass_rate", 0.0)

        if status == "pass":
            rb.add("correct_solution", +50.0, "All test cases passed")

            avg_time = hidden_result.get("avg_time", 1.0)
            if avg_time < 2.0:
                time_bonus = (2.0 - avg_time) * 10
                rb.add("fast_execution_bonus", round(time_bonus, 2), f"Dynamic time bonus for {avg_time:.3f}s")

        elif status == "tle":
            rb.add("time_limit_exceeded", -20.0,
                   "Brute force — no algorithmic thinking")

        elif status in ("fail", "error"):
            # Partial credit for partial pass rate
            if hidden_pass_rate > 0:
                partial = round(hidden_pass_rate * 20, 1)
                rb.add("partial_pass", partial,
                       f"Passed {hidden_pass_rate*100:.0f}% of hidden test cases")
            rb.add("wrong_answer", -10.0, "Wrong answer on at least one test")

        if public_pass_rate > hidden_pass_rate:
            rb.add("hidden_test_regression", -6.0, "Passes public tests but regresses on hidden tests")

        # Syntax error penalty
        results = hidden_result.get("results", [])
        has_stderr = any(r.get("stderr") for r in results)
        if has_stderr and status == "error":
            rb.add("syntax_error", -5.0, "Code has syntax/runtime errors")

        normalized = solver_code.lower()
        for pattern, penalty, reason in self.FORBIDDEN_PATTERNS:
            if pattern in normalized:
                rb.add("forbidden_pattern", penalty, reason)

        avg_memory_mb = hidden_result.get("avg_memory_mb", 0.0)
        if avg_memory_mb > 50.0:
            penalty = -min(20.0, (avg_memory_mb - 50.0) * 0.5)
            rb.add("high_memory_penalty", round(penalty, 1), f"High memory usage: {avg_memory_mb:.1f}MB")

        loop_depth, uses_fast_io, if_count = self._estimate_algorithmic_risk(solver_code)
        
        if if_count > 5:
            rb.add("cyclomatic_complexity", -5.0, "Excessive if/else branching detected")
            
        optimal_rank = self._complexity_rank(optimal_complexity)
        if optimal_rank <= self._complexity_rank("O(N log N)") and loop_depth >= 2:
            rb.add("complexity_risk", -8.0, "Nested loops suggest a brute-force strategy")
        elif status == "pass" and loop_depth <= 1:
            rb.add("complexity_match", +6.0, "Control flow matches the expected complexity tier")

        if uses_fast_io:
            rb.add("fast_io_bonus", +2.0, "Uses fast stdin handling")

        if "if __name__" in normalized:
            rb.add("entrypoint_bonus", +1.0, "Uses a clean script entrypoint")

        return rb
