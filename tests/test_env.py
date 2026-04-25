"""Tests for the CodeCourt environment."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.codecourt_env import CodeCourtEnv
from agents.setter import SetterAgent
from agents.solver import SolverAgent


def test_env_reset():
    env = CodeCourtEnv()
    obs = env.reset()
    assert "episode_id" in obs
    assert "archetype" in obs
    assert "difficulty" in obs
    assert "public_test_cases" in obs
    assert "hidden_test_count" in obs
    print("✓ test_env_reset")


def test_env_step():
    env = CodeCourtEnv()
    obs = env.reset()
    
    setter = SetterAgent(use_reference=True)
    solver = SolverAgent(use_reference=True)
    
    setter_code = setter.generate_solution(env._current_state.problem)
    solver_code = solver.solve(env._current_state.problem)
    
    setter_info, solver_info, done, info = env.step(setter_code, solver_code)
    
    assert done == True
    assert "outcome" in info
    assert "setter_valid" in info
    assert "solver_public_pass_rate" in info
    assert "solver_hidden_pass_rate" in info
    print("✓ test_env_step")


def test_difficulty_progression():
    env = CodeCourtEnv(difficulty_progression=True)
    setter = SetterAgent(use_reference=True)
    solver = SolverAgent(use_reference=True)
    
    # With reference solutions for both, solver will always pass
    # This tests that the difficulty progression logic runs
    for _ in range(10):
        obs = env.reset()
        setter_code = setter.generate_solution(env._current_state.problem)
        solver_code = solver.solve(env._current_state.problem)
        env.step(setter_code, solver_code)
    
    # Just verify the environment ran without errors
    assert env._episode_count == 10
    print("✓ test_difficulty_progression")


def test_elo_tracker():
    env = CodeCourtEnv()
    setter = SetterAgent(use_reference=True)
    solver = SolverAgent(use_reference=True)
    
    for _ in range(10):
        obs = env.reset()
        setter_code = setter.generate_solution(env._current_state.problem)
        solver_code = solver.solve(env._current_state.problem)
        env.step(setter_code, solver_code)
    
    stats = env.elo.get_stats()
    assert "setter_elo" in stats
    assert "solver_elo" in stats
    assert stats["episodes"] == 10
    print("✓ test_elo_tracker")


if __name__ == "__main__":
    print("Running Environment tests...")
    test_env_reset()
    test_env_step()
    test_difficulty_progression()
    test_elo_tracker()
    print("\n✅ All environment tests passed!")
