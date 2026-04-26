"""
Setter Agent — generates problems and reference solutions.
Falls back to reference solutions for testing.
"""

from typing import Optional, Dict, Any
from agents.prompts import (
    SETTER_SYSTEM,
    SETTER_USER_TEMPLATE,
    REFERENCE_SOLUTIONS,
)


class SetterAgent:
    """
    Setter agent wrapper.
    Uses LLM if available; falls back to reference for testing.
    """

    def __init__(
        self,
        model=None,
        tokenizer=None,
        use_reference: bool = False,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.use_reference = use_reference or (model is None)

    def generate_solution(self, problem: Dict[str, Any]) -> str:
        """
        Given a problem dict, return Python code that solves it.
        This is the Setter's reference solution.
        """
        if self.use_reference:
            return self._reference_solution(problem)

        return self._llm_generate(problem)

    def _reference_solution(self, problem: Dict[str, Any]) -> str:
        if problem.get("reference_solution"):
            return problem["reference_solution"]
        archetype = problem.get("archetype", "array")
        task_id = problem.get("task_id", 0)
        key = (archetype, task_id)
        return REFERENCE_SOLUTIONS.get(key, 'print(0)')

    def _llm_generate(self, problem: Dict[str, Any]) -> str:
        archetype = problem.get("archetype", "array")
        task_id = problem.get("task_id", 0)
        difficulty = problem.get("difficulty", 1)
        
        # Get task info
        from env.problem_types import ARCHETYPES
        task = ARCHETYPES[archetype]["tasks"][task_id]
        
        # Build prompt
        test_cases = problem.get("test_cases", [])
        sample_input = test_cases[0]["input"] if test_cases else ""
        sample_output = test_cases[0]["expected"] if test_cases else ""
        
        prompt = SETTER_USER_TEMPLATE.format(
            archetype=archetype,
            task=task["name"],
            difficulty=difficulty,
            description=problem["description"],
            sample_input=sample_input,
            sample_output=sample_output,
        )

        messages = [
            {"role": "system", "content": SETTER_SYSTEM},
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
        archetype = problem.get("archetype", "array")
        task_id = problem.get("task_id", 0)
        difficulty = problem.get("difficulty", 1)
        
        from env.problem_types import ARCHETYPES
        task = ARCHETYPES[archetype]["tasks"][task_id]
        
        test_cases = problem.get("test_cases", [])
        sample_input = test_cases[0]["input"] if test_cases else ""
        sample_output = test_cases[0]["expected"] if test_cases else ""
        
        return SETTER_SYSTEM + "\n\n" + SETTER_USER_TEMPLATE.format(
            archetype=archetype,
            task=task["name"],
            difficulty=difficulty,
            description=problem["description"],
            sample_input=sample_input,
            sample_output=sample_output,
        )
