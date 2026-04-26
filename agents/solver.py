"""
Solver Agent — writes code solutions to problems.
Falls back to reference or brute-force solutions for testing.
"""

from typing import Optional, Dict, Any
from agents.prompts import (
    SOLVER_SYSTEM,
    SOLVER_USER_TEMPLATE,
    REFERENCE_SOLUTIONS,
    BRUTE_FORCE_SOLUTIONS,
)


class SolverAgent:
    """
    Solver agent wrapper.
    Uses LLM if available; falls back to reference/brute-force for testing.
    """

    def __init__(
        self,
        model=None,
        tokenizer=None,
        use_reference: bool = False,
        use_brute_force: bool = False,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.use_reference = use_reference or (model is None and not use_brute_force)
        self.use_brute_force = use_brute_force

    def solve(self, problem: Dict[str, Any]) -> str:
        """
        Given a problem dict, return Python code that attempts to solve it.
        """
        if self.use_brute_force:
            return self._brute_force(problem)

        if self.use_reference:
            return self._reference_solution(problem)

        return self._llm_solve(problem)

    def _reference_solution(self, problem: Dict[str, Any]) -> str:
        if problem.get("reference_solution"):
            return problem["reference_solution"]
        archetype = problem.get("archetype", "array")
        task_id = problem.get("task_id", 0)
        key = (archetype, task_id)
        return REFERENCE_SOLUTIONS.get(key, 'print(0)')

    def _brute_force(self, problem: Dict[str, Any]) -> str:
        if problem.get("brute_force_solution"):
            return problem["brute_force_solution"]
        archetype = problem.get("archetype", "array")
        task_id = problem.get("task_id", 0)
        key = (archetype, task_id)
        if key in BRUTE_FORCE_SOLUTIONS:
            return BRUTE_FORCE_SOLUTIONS[key]
        return "print(0)"

    def _llm_solve(self, problem: Dict[str, Any]) -> str:
        prompt = SOLVER_USER_TEMPLATE.format(
            description=problem["description"]
        )

        messages = [
            {"role": "system", "content": SOLVER_SYSTEM},
            {"role": "user", "content": prompt},
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True,
        ).to(self.model.device)

        outputs = self.model.generate(
            inputs,
            max_new_tokens=512,
            temperature=0.8,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        generated = self.tokenizer.decode(
            outputs[0][inputs.shape[1]:],
            skip_special_tokens=True,
        )

        return self._clean_code(generated)

    @staticmethod
    def _clean_code(raw: str) -> str:
        lines = raw.strip().split('\n')
        cleaned = []
        in_fence = False
        for line in lines:
            if line.strip().startswith('```'):
                in_fence = not in_fence
                continue
            cleaned.append(line)
        return '\n'.join(cleaned).strip()

    def build_prompt_text(self, problem: Dict[str, Any]) -> str:
        return SOLVER_SYSTEM + "\n\n" + SOLVER_USER_TEMPLATE.format(
            description=problem["description"]
        )
