"""
Episode state — tracks everything that happens in one CodeCourt round.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class EpisodeState:
    # Identifiers
    episode_id: int
    archetype: str
    task_id: int
    difficulty: int

    # Problem
    problem: Optional[Dict[str, Any]] = None

    # Setter
    setter_code: Optional[str] = None
    setter_result: Optional[Dict] = None
    setter_reward: float = 0.0
    setter_valid: bool = False

    # Solver
    solver_code: Optional[str] = None
    solver_public_result: Optional[Dict] = None
    solver_hidden_result: Optional[Dict] = None
    solver_result: Optional[Dict] = None
    solver_reward: float = 0.0

    # Episode outcome
    done: bool = False
    outcome: str = "pending"  # 'setter_wins' | 'solver_wins' | 'invalid'

    # History
    history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "archetype": self.archetype,
            "task_id": self.task_id,
            "difficulty": self.difficulty,
            "setter_reward": self.setter_reward,
            "solver_reward": self.solver_reward,
            "outcome": self.outcome,
            "done": self.done,
            "setter_valid": self.setter_valid,
            "solver_passed": (
                self.solver_hidden_result.get("overall_status") == "pass"
                if self.solver_hidden_result else False
            ),
        }
