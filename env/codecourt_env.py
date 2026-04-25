"""
CodeCourtEnv — OpenEnv-compliant environment.
Implements reset / step / render following the OpenEnv spec.
"""

import random
from typing import Dict, Any, Optional, Tuple

from env.problem_types import ARCHETYPES, build_problem
from env.state import EpisodeState
from oracle.executor import OracleExecutor
from oracle.validator import ProblemValidator
from rewards.rubrics import SetterRubric, SolverRubric
from rewards.elo import EloTracker


class CodeCourtEnv:
    """
    Adversarial Curriculum Arena environment.

    Two LLM agents compete:
      - Setter: generates a problem + test cases
      - Solver: writes code to solve the problem

    Minimax rewards:
      - Setter wins  (+50) if Solver fails AND Setter can solve it
      - Solver wins  (+50) if it passes all test cases
    """

    ENV_NAME = "codecourt-v1"
    VERSION = "1.0.0"

    def __init__(
        self,
        archetypes: Optional[list] = None,
        time_limit: float = 2.0,
        memory_limit_mb: int = 256,
        difficulty_progression: bool = True,
        seed: int = 42,
    ):
        self.archetypes = archetypes or list(ARCHETYPES.keys())
        self.oracle = OracleExecutor(time_limit, memory_limit_mb)
        self.validator = ProblemValidator()
        self.setter_rubric = SetterRubric()
        self.solver_rubric = SolverRubric()
        self.elo = EloTracker()
        self.difficulty_progression = difficulty_progression
        self.rng = random.Random(seed)

        self._episode_count = 0
        self._current_state: Optional[EpisodeState] = None
        self._current_difficulty = 1
        self._solver_pass_streak = 0

    # ──────────────────────────────────────────────────────────
    # OpenEnv Interface
    # ──────────────────────────────────────────────────────────

    def reset(self) -> Dict[str, Any]:
        """Start a new episode. Returns initial observation."""
        archetype = self.rng.choice(self.archetypes)
        task_id = self.rng.randint(0, len(ARCHETYPES[archetype]["tasks"]) - 1)
        variant_seed = self.rng.randint(0, 10**9)

        self._current_state = EpisodeState(
            episode_id=self._episode_count,
            archetype=archetype,
            task_id=task_id,
            difficulty=self._current_difficulty,
        )
        self._episode_count += 1

        # Build the ground-truth problem (Setter starts from this template)
        problem = build_problem(archetype, task_id, self._current_difficulty, seed=variant_seed)
        self._current_state.problem = problem

        obs = {
            "episode_id": self._current_state.episode_id,
            "archetype": archetype,
            "task_id": task_id,
            "difficulty": self._current_difficulty,
            "problem_template": problem["description"],
            "public_test_cases": problem["public_test_cases"],
            "hidden_test_count": len(problem["hidden_test_cases"]),
            "variant_seed": variant_seed,
            "elo": self.elo.get_stats(),
        }
        return obs

    def step(
        self,
        setter_code: str,
        solver_code: str,
    ) -> Tuple[Dict, Dict, bool, Dict]:
        """
        Run one full episode step:
          1. Validate problem
          2. Run setter_code against test cases (self-consistency)
          3. Run solver_code against test cases
          4. Compute rewards
          5. Update Elo, difficulty

        Returns: (setter_reward_info, solver_reward_info, done, info)
        """
        state = self._current_state
        assert state is not None, "Call reset() before step()"

        problem = state.problem
        public_test_cases = problem.get("public_test_cases", problem["test_cases"])
        hidden_test_cases = problem.get("hidden_test_cases", problem["test_cases"])
        all_test_cases = public_test_cases + hidden_test_cases

        # ── 1. Validate problem structure ──
        validation = self.validator.validate(problem)
        state.setter_valid = validation.valid

        # ── 2. Setter self-consistency check ──
        setter_run = self.oracle.run_against_tests(setter_code, all_test_cases)
        state.setter_code = setter_code
        state.setter_result = setter_run

        # ── 3. Solver attempts ──
        solver_public_run = self.oracle.run_against_tests(solver_code, public_test_cases)
        solver_hidden_run = self.oracle.run_against_tests(solver_code, hidden_test_cases)
        solver_run = self.oracle.run_against_tests(solver_code, all_test_cases)
        state.solver_code = solver_code
        state.solver_public_result = solver_public_run
        state.solver_hidden_result = solver_hidden_run
        state.solver_result = solver_run

        # ── 4. Rewards ──
        setter_breakdown = self.setter_rubric.score(
            setter_result=setter_run,
            solver_public_result=solver_public_run,
            solver_hidden_result=solver_hidden_run,
            problem_valid=state.setter_valid,
            optimal_complexity=problem.get("optimal_complexity", "O(N)"),
        )
        solver_breakdown = self.solver_rubric.score(
            public_result=solver_public_run,
            hidden_result=solver_hidden_run,
            solver_code=solver_code,
            optimal_complexity=problem.get("optimal_complexity", "O(N)"),
        )

        state.setter_reward = setter_breakdown.total
        state.solver_reward = solver_breakdown.total

        # ── 5. Determine outcome ──
        solver_passed = solver_hidden_run["overall_status"] == "pass"
        setter_can_solve = setter_run["overall_status"] == "pass"

        if not state.setter_valid or not setter_can_solve:
            state.outcome = "invalid"
        elif solver_passed:
            state.outcome = "solver_wins"
            self._solver_pass_streak += 1
        else:
            state.outcome = "setter_wins"
            self._solver_pass_streak = 0

        # ── 6. Update Elo ──
        self.elo.update(
            setter_won=(state.outcome == "setter_wins"),
            setter_reward=state.setter_reward,
            solver_reward=state.solver_reward,
        )

        # ── 7. Difficulty progression ──
        if self.difficulty_progression:
            if self._solver_pass_streak >= 3 and self._current_difficulty < 3:
                self._current_difficulty += 1
                self._solver_pass_streak = 0

        state.done = True

        info = {
            "outcome": state.outcome,
            "setter_valid": state.setter_valid,
            "setter_pass_rate": setter_run["pass_rate"],
            "solver_public_pass_rate": solver_public_run["pass_rate"],
            "solver_hidden_pass_rate": solver_hidden_run["pass_rate"],
            "solver_pass_rate": solver_hidden_run["pass_rate"],
            "difficulty": self._current_difficulty,
            "elo": self.elo.get_stats(),
            "validation_errors": validation.errors,
            "validation_warnings": validation.warnings,
        }

        return (
            {"reward": state.setter_reward, "breakdown": setter_breakdown.__dict__},
            {"reward": state.solver_reward, "breakdown": solver_breakdown.__dict__},
            True,  # done — one step per episode
            info,
        )

    def render(self, mode: str = "text") -> str:
        """Human-readable state summary."""
        s = self._current_state
        if s is None:
            return "No active episode. Call reset() first."

        lines = [
            f"═══ Episode {s.episode_id} ═══",
            f"Archetype : {s.archetype} / Task {s.task_id} / Difficulty {s.difficulty}",
            f"Outcome   : {s.outcome}",
            f"Setter R  : {s.setter_reward:+.1f}",
            f"Solver R  : {s.solver_reward:+.1f}",
            f"Elo       : Setter={self.elo.setter_elo:.0f} "
            f"Solver={self.elo.solver_elo:.0f}",
        ]
        return "\n".join(lines)

    def get_metrics(self) -> Dict[str, Any]:
        """Return aggregate training metrics."""
        return {
            "total_episodes": self._episode_count,
            "current_difficulty": self._current_difficulty,
            **self.elo.get_stats(),
        }
