"""
Elo tracker for Setter vs Solver across episodes.
Also tracks problem difficulty score and reward history.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class AgentStats:
    name: str
    elo: float = 1000.0
    wins: int = 0
    losses: int = 0
    total_reward: float = 0.0
    reward_history: List[float] = field(default_factory=list)

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0


class EloTracker:
    """
    Tracks Elo ratings and reward history for both agents.
    K-factor = 32 (standard chess K for new players).
    """

    K = 32

    def __init__(self):
        self.setter = AgentStats("setter")
        self.solver = AgentStats("solver")
        self._episode_count = 0
        self.difficulty_history: List[int] = []

    @property
    def setter_elo(self) -> float:
        return self.setter.elo

    @property
    def solver_elo(self) -> float:
        return self.solver.elo

    def _expected(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))

    def update(
        self,
        setter_won: bool,
        setter_reward: float,
        solver_reward: float,
        difficulty: int = 1,
    ):
        """Update Elo ratings after one episode."""
        self._episode_count += 1
        self.difficulty_history.append(difficulty)

        # Track rewards
        self.setter.reward_history.append(setter_reward)
        self.solver.reward_history.append(solver_reward)
        self.setter.total_reward += setter_reward
        self.solver.total_reward += solver_reward

        # Elo update
        e_setter = self._expected(self.setter.elo, self.solver.elo)
        e_solver = 1 - e_setter

        if setter_won:
            s_setter, s_solver = 1.0, 0.0
            self.setter.wins += 1
            self.solver.losses += 1
        else:
            s_setter, s_solver = 0.0, 1.0
            self.solver.wins += 1
            self.setter.losses += 1

        self.setter.elo += self.K * (s_setter - e_setter)
        self.solver.elo += self.K * (s_solver - e_solver)

    def get_stats(self) -> Dict:
        return {
            "setter_elo": round(self.setter.elo, 1),
            "solver_elo": round(self.solver.elo, 1),
            "setter_wins": self.setter.wins,
            "solver_wins": self.solver.wins,
            "setter_win_rate": round(self.setter.win_rate, 3),
            "solver_win_rate": round(self.solver.win_rate, 3),
            "setter_avg_reward": round(
                self.setter.total_reward / max(self._episode_count, 1), 2
            ),
            "solver_avg_reward": round(
                self.solver.total_reward / max(self._episode_count, 1), 2
            ),
            "episodes": self._episode_count,
        }

    def reward_curve(self, window: int = 10) -> Dict[str, List[float]]:
        """Return smoothed reward curves for plotting."""
        def smooth(arr, w):
            result = []
            for i in range(len(arr)):
                start = max(0, i - w + 1)
                result.append(sum(arr[start:i+1]) / (i - start + 1))
            return result

        return {
            "setter": smooth(self.setter.reward_history, window),
            "solver": smooth(self.solver.reward_history, window),
            "episodes": list(range(len(self.setter.reward_history))),
        }