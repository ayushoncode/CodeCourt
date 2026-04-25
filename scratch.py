from env.codecourt_env import CodeCourtEnv
from agents.setter import SetterAgent

env = CodeCourtEnv()
obs = env.reset()
setter = SetterAgent(use_reference=True)
problem = env._current_state.problem
setter_code = setter.generate_solution(problem)

print("--- Setter Code ---")
print(setter_code)

res = env.oracle.run_against_tests(setter_code, problem["test_cases"])
print("\n--- Oracle Result ---")
for r in res["results"]:
    print(r["status"], r["passed"], r["stderr"])

