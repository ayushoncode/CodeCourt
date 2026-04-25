"""
Problem Validator — checks that Setter-generated problems
are well-formed before sending to Solver.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class ProblemValidator:
    """
    Validates that a generated problem has required fields
    and sensible constraints.
    """

    REQUIRED_FIELDS = ['title', 'description', 'input_format',
                       'output_format', 'constraints', 'archetype']

    def validate(self, problem: dict) -> ValidationResult:
        result = ValidationResult(valid=True)

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in problem or not problem[field]:
                result.add_error(f"Missing required field: {field}")

        public_test_cases = problem.get('public_test_cases', [])
        hidden_test_cases = problem.get('hidden_test_cases', [])
        test_cases = problem.get('test_cases', [])
        combined_cases = test_cases or (public_test_cases + hidden_test_cases)

        # Check test cases exist
        if not combined_cases:
            result.add_error("No test cases provided")
        elif len(combined_cases) < 2:
            result.add_warning("Only 1 test case — consider adding edge cases")

        if public_test_cases and hidden_test_cases:
            if len(public_test_cases) < 1:
                result.add_error("At least 1 public test case is required")
            if len(hidden_test_cases) < 1:
                result.add_error("At least 1 hidden test case is required")

        # Validate each test case has input and expected
        for i, tc in enumerate(combined_cases):
            if 'input' not in tc:
                result.add_error(f"Test case {i+1} missing 'input'")
            if 'expected' not in tc:
                result.add_error(f"Test case {i+1} missing 'expected'")

        # Check difficulty is within range
        difficulty = problem.get('difficulty', 0)
        if not (1 <= difficulty <= 9):
            result.add_warning(f"Difficulty {difficulty} outside expected 1-9 range")

        # Check archetype is known
        from env.problem_types import ARCHETYPES
        if problem.get('archetype') not in ARCHETYPES:
            result.add_error(
                f"Unknown archetype: {problem.get('archetype')}. "
                f"Must be one of: {list(ARCHETYPES.keys())}"
            )

        return result
