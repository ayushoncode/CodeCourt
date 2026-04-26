"""
FastAPI app for the CodeCourt Hugging Face Docker Space.
"""

from __future__ import annotations

import json
import threading
import uuid
import random
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agents import SetterAgent, SolverAgent
from env import CodeCourtEnv
from env.problem_types import ARCHETYPES, build_problem
from env.state import EpisodeState


APP_ROOT = Path(__file__).resolve().parent
DASHBOARD_DIR = APP_ROOT / "dashboard"
README_PATH = APP_ROOT / "README.md"
OPENENV_PATH = APP_ROOT / "openenv.yaml"
OUTPUTS_DIR = APP_ROOT / "outputs"


class SessionCreateRequest(BaseModel):
    archetype: Optional[str] = None
    task_id: Optional[int] = Field(default=None, ge=0)
    difficulty: int = Field(default=1, ge=1, le=3)
    seed: int = 42


class SolverRunRequest(BaseModel):
    solver_mode: str = Field(default="brute_force")
    setter_mode: str = Field(default="reference")
    solver_code: Optional[str] = None
    setter_code: Optional[str] = None


class BenchmarkRequest(BaseModel):
    episodes: int = Field(default=6, ge=1, le=30)
    solver_mode: str = Field(default="brute_force")
    seed: int = 42


class SessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, CodeCourtEnv] = {}
        self._lock = threading.Lock()

    def put(self, env: CodeCourtEnv) -> str:
        session_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._sessions[session_id] = env
        return session_id

    def get(self, session_id: str) -> CodeCourtEnv:
        with self._lock:
            env = self._sessions.get(session_id)
        if env is None:
            raise KeyError(session_id)
        return env


app = FastAPI(title="CodeCourt", version="1.0.0")
app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR), html=False), name="outputs")
SESSIONS = SessionStore()

active_connections: list[WebSocket] = []

@app.websocket("/ws/arena")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.post("/api/internal/broadcast")
async def internal_broadcast(request: Request):
    data = await request.json()
    for conn in active_connections.copy():
        try:
            await conn.send_json(data)
        except Exception:
            if conn in active_connections:
                active_connections.remove(conn)
    return JSONResponse(content={"status": "broadcasted"})


def _new_env(seed: int, difficulty: int) -> CodeCourtEnv:
    env = CodeCourtEnv(difficulty_progression=False, seed=seed)
    env._current_difficulty = difficulty
    return env


def _get_session_env(session_id: str) -> CodeCourtEnv:
    try:
        return SESSIONS.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown session_id: {session_id}") from exc


def _force_problem(
    env: CodeCourtEnv,
    *,
    archetype: Optional[str],
    task_id: Optional[int],
    difficulty: int,
) -> Dict[str, Any]:
    if archetype is None:
        obs = env.reset()
        return obs

    if archetype not in ARCHETYPES:
        raise HTTPException(status_code=400, detail=f"Unknown archetype: {archetype}")

    max_task_id = len(ARCHETYPES[archetype]["tasks"]) - 1
    chosen_task_id = 0 if task_id is None else task_id
    if not (0 <= chosen_task_id <= max_task_id):
        raise HTTPException(status_code=400, detail=f"task_id must be between 0 and {max_task_id}")

    env._current_state = EpisodeState(
        episode_id=env._episode_count,
        archetype=archetype,
        task_id=chosen_task_id,
        difficulty=difficulty,
    )
    env._episode_count += 1
    variant_seed = env.rng.randint(0, 10**9)
    problem = build_problem(archetype, chosen_task_id, difficulty, seed=variant_seed)
    env._current_state.problem = problem
    return {
        "episode_id": env._current_state.episode_id,
        "archetype": archetype,
        "task_id": chosen_task_id,
        "difficulty": difficulty,
        "problem_template": problem["description"],
        "test_cases": problem["test_cases"],
        "variant_seed": variant_seed,
        "elo": env.elo.get_stats(),
    }


def _truncate_problem(problem: dict) -> dict:
    return {
        "title": problem.get("title"),
        "description": problem.get("description"),
        "constraints": problem.get("constraints"),
        "input_format": problem.get("input_format"),
        "output_format": problem.get("output_format"),
        "optimal_complexity": problem.get("optimal_complexity"),
        "variant_seed": problem.get("variant_seed"),
        "public_test_cases": problem.get("public_test_cases", problem.get("test_cases", []))[:3],
        "public_test_count": len(problem.get("public_test_cases", problem.get("test_cases", []))),
        "hidden_test_count": len(problem.get("hidden_test_cases", [])),
    }


def _serialize_state(env: CodeCourtEnv) -> dict:
    state = env._current_state
    if state is None:
        raise HTTPException(status_code=400, detail="Session has no active episode")

    payload = state.to_dict()
    payload["problem"] = _truncate_problem(state.problem or {})
    payload["elo"] = env.elo.get_stats()
    payload["rendered"] = env.render()
    if state.setter_result:
        payload["setter_result"] = state.setter_result
    if state.solver_result:
        payload["solver_result"] = state.solver_result
    if state.setter_code:
        payload["setter_code"] = state.setter_code
    if state.solver_code:
        payload["solver_code"] = state.solver_code
    return payload


def _build_demo_snapshot() -> dict:
    env = _new_env(seed=42, difficulty=1)
    obs = env.reset()
    problem = env._current_state.problem
    return {
        "environment": CodeCourtEnv.ENV_NAME,
        "version": CodeCourtEnv.VERSION,
        "episode": {
            "episode_id": obs["episode_id"],
            "archetype": obs["archetype"],
            "task_id": obs["task_id"],
            "difficulty": obs["difficulty"],
            "problem_template": obs["problem_template"],
            "problem": _truncate_problem(problem),
        },
        "elo": obs["elo"],
    }


def _build_overview() -> dict:
    return {
        "environment": {
            "name": CodeCourtEnv.ENV_NAME,
            "version": CodeCourtEnv.VERSION,
            "agent_count": 2,
            "archetype_count": len(ARCHETYPES),
            "task_count": sum(len(arch["tasks"]) for arch in ARCHETYPES.values()),
            "difficulty_tiers": 3,
        },
        "agents": [
            {
                "name": "Setter",
                "role": "Problem generator",
                "goal": "Produce valid tasks and adversarial hidden tests that expose solver weaknesses.",
            },
            {
                "name": "Solver",
                "role": "Code generator",
                "goal": "Write efficient Python that passes all hidden and public tests.",
            },
        ],
        "story": {
            "problem": "LLMs often look strong on known coding tasks but fail on adversarial hidden edge cases.",
            "intervention": "CodeCourt trains against those failures using dynamic hidden tests, reward shaping, and sandboxed execution.",
            "result": "The system can show baseline weakness, training-time improvement, and before-vs-after metrics in one demo.",
            "why_hard_to_game": "Seeded task variation and hidden tests reduce memorization and punish public-only overfitting.",
        },
        "training_pipeline": [
            "Generate a task template and seeded dynamic test set with adversarial hidden cases.",
            "Collect solver completions from the policy being trained.",
            "Execute code in the Oracle sandbox and measure correctness, robustness, and pass rate.",
            "Transform execution outcomes into shaped GRPO rewards and update the solver policy.",
            "Save baseline, manifests, summaries, and before/after plots for judge-facing proof.",
        ],
    }


def _build_walkthrough() -> dict:
    dynamic_seed = random.randint(0, 10**9)
    env = _new_env(seed=dynamic_seed, difficulty=1)
    obs = _force_problem(env, archetype=None, task_id=None, difficulty=1)
    problem = env._current_state.problem

    setter = SetterAgent(use_reference=True)
    brute_solver = SolverAgent(use_brute_force=True)
    optimal_solver = SolverAgent(use_reference=True)

    setter_code = setter.generate_solution(problem)
    brute_code = brute_solver.solve(problem)
    optimal_code = optimal_solver.solve(problem)

    _, brute_solver_info, _, brute_info = env.step(setter_code, brute_code)

    eval_env = _new_env(seed=dynamic_seed, difficulty=1)
    _force_problem(eval_env, archetype=obs["archetype"], task_id=obs["task_id"], difficulty=obs["difficulty"])
    setter_eval_code = setter.generate_solution(eval_env._current_state.problem)
    _, optimal_solver_info, _, optimal_info = eval_env.step(setter_eval_code, optimal_code)

    return {
        "problem": {
            "archetype": obs["archetype"],
            "task_id": obs["task_id"],
            "difficulty": obs["difficulty"],
            **_truncate_problem(problem),
        },
        "runs": [
            {
                "label": "Baseline Solver",
                "solver_mode": "brute_force",
                "outcome": brute_info["outcome"],
                "solver_reward": brute_solver_info["reward"],
                "solver_pass_rate": brute_info["solver_pass_rate"],
                "setter_valid": brute_info["setter_valid"],
                "validation_errors": brute_info["validation_errors"],
            },
            {
                "label": "Reference Solver",
                "solver_mode": "optimal_reference",
                "outcome": optimal_info["outcome"],
                "solver_reward": optimal_solver_info["reward"],
                "solver_pass_rate": optimal_info["solver_pass_rate"],
                "setter_valid": optimal_info["setter_valid"],
                "validation_errors": optimal_info["validation_errors"],
            },
        ],
    }


def _read_json_if_exists(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def _build_artifacts() -> dict:
    baseline_path = OUTPUTS_DIR / "baseline_results.json"
    training_log_path = OUTPUTS_DIR / "training_history.json"
    manifest_path = OUTPUTS_DIR / "artifact_manifest.json"
    training_summary_path = OUTPUTS_DIR / "training_summary.json"
    capability_eval_path = OUTPUTS_DIR / "capability_boundary_eval.json"
    plots_dir = OUTPUTS_DIR / "plots"
    evaluation_summary_path = plots_dir / "evaluation_summary.json"

    baseline = _read_json_if_exists(baseline_path)
    training_log = _read_json_if_exists(training_log_path)
    manifest = _read_json_if_exists(manifest_path)
    evaluation_summary = _read_json_if_exists(evaluation_summary_path)
    training_summary = _read_json_if_exists(training_summary_path)
    if training_summary is None and isinstance(evaluation_summary, dict):
        training_summary = evaluation_summary
    capability_eval = _read_json_if_exists(capability_eval_path)

    latest_reward = None
    latest_pass_rate = None
    if isinstance(training_log, list) and training_log:
        reward_rows = [row for row in training_log if isinstance(row, dict)]
        if reward_rows:
            latest = reward_rows[-1]
            latest_reward = latest.get("solver_reward", latest.get("reward"))
            latest_pass_rate = latest.get("solver_pass_rate", latest.get("reward_pass_rate"))

    return {
        "baseline_available": baseline is not None,
        "training_manifest_available": manifest is not None,
        "training_log_available": training_log is not None,
        "training_summary_available": training_summary is not None,
        "plots_available": plots_dir.exists(),
        "baseline_summary": baseline.get("summary") if isinstance(baseline, dict) else None,
        "training_manifest": manifest,
        "training_summary": training_summary,
        "evaluation_summary": evaluation_summary,
        "capability_eval": capability_eval,
        "latest_training_metrics": {
            "reward": latest_reward,
            "reward_pass_rate": latest_pass_rate,
        },
        "plot_files": sorted([p.name for p in plots_dir.glob("*")]) if plots_dir.exists() else [],
    }


def _select_setter(problem: dict, request: SolverRunRequest) -> str:
    if request.setter_code:
        return request.setter_code
    setter = SetterAgent(use_reference=True)
    return setter.generate_solution(problem)


def _select_solver(problem: dict, request: SolverRunRequest) -> str:
    if request.solver_mode == "custom":
        if not request.solver_code:
            raise HTTPException(status_code=400, detail="solver_code is required for custom mode")
        return request.solver_code
    if request.solver_mode == "reference":
        return SolverAgent(use_reference=True).solve(problem)
    if request.solver_mode == "brute_force":
        return SolverAgent(use_brute_force=True).solve(problem)
    raise HTTPException(status_code=400, detail=f"Unknown solver_mode: {request.solver_mode}")


def _run_episode(env: CodeCourtEnv, request: SolverRunRequest) -> dict:
    state = env._current_state
    if state is None or state.problem is None:
        raise HTTPException(status_code=400, detail="Reset the session before running a solver")

    setter_code = _select_setter(state.problem, request)
    solver_code = _select_solver(state.problem, request)
    setter_info, solver_info, _, info = env.step(setter_code, solver_code)

    return {
        "session_state": _serialize_state(env),
        "info": info,
        "setter_reward_info": setter_info,
        "solver_reward_info": solver_info,
    }


def _benchmark(request: BenchmarkRequest) -> dict:
    setter = SetterAgent(use_reference=True)
    episodes = []

    for episode_idx in range(request.episodes):
        env = _new_env(seed=request.seed + episode_idx, difficulty=1)
        obs = env.reset()
        problem = env._current_state.problem
        setter_code = setter.generate_solution(problem)
        solver_request = SolverRunRequest(solver_mode=request.solver_mode)
        solver_code = _select_solver(problem, solver_request)
        _, solver_info, _, info = env.step(setter_code, solver_code)
        effective_pass_rate = 0.0 if info["outcome"] == "invalid" else info["solver_pass_rate"]
        episodes.append({
            "episode": episode_idx,
            "archetype": obs["archetype"],
            "task_id": obs["task_id"],
            "difficulty": obs["difficulty"],
            "outcome": info["outcome"],
            "solver_reward": solver_info["reward"],
            "solver_pass_rate": effective_pass_rate,
            "raw_solver_pass_rate": info["solver_pass_rate"],
        })

    avg_pass_rate = sum(ep["solver_pass_rate"] for ep in episodes) / len(episodes)
    avg_reward = sum(ep["solver_reward"] for ep in episodes) / len(episodes)
    return {
        "solver_mode": request.solver_mode,
        "episodes": episodes,
        "summary": {
            "episodes": request.episodes,
            "avg_solver_pass_rate": avg_pass_rate,
            "avg_solver_reward": avg_reward,
            "solver_win_rate": sum(1 for ep in episodes if ep["outcome"] == "solver_wins") / len(episodes),
            "setter_win_rate": sum(1 for ep in episodes if ep["outcome"] == "setter_wins") / len(episodes),
            "invalid_rate": sum(1 for ep in episodes if ep["outcome"] == "invalid") / len(episodes),
        },
    }


@app.get("/")
def root() -> FileResponse:
    return FileResponse(DASHBOARD_DIR / "index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": "codecourt-space"}


@app.get("/api/overview")
def overview() -> JSONResponse:
    return JSONResponse(content=_build_overview())


@app.get("/api/spec", response_class=PlainTextResponse)
def spec() -> PlainTextResponse:
    if not OPENENV_PATH.exists():
        raise HTTPException(status_code=404, detail="openenv.yaml not found")
    return PlainTextResponse(OPENENV_PATH.read_text(), media_type="text/yaml")


@app.get("/api/readme", response_class=PlainTextResponse)
def readme() -> PlainTextResponse:
    if not README_PATH.exists():
        raise HTTPException(status_code=404, detail="README.md not found")
    return PlainTextResponse(README_PATH.read_text(), media_type="text/markdown")


@app.get("/api/demo")
def demo() -> JSONResponse:
    return JSONResponse(content=_build_demo_snapshot())


@app.get("/api/walkthrough")
def walkthrough() -> JSONResponse:
    return JSONResponse(content=_build_walkthrough())


@app.get("/api/artifacts")
def artifacts() -> JSONResponse:
    return JSONResponse(content=_build_artifacts())


@app.post("/api/session")
def create_session(request: SessionCreateRequest) -> JSONResponse:
    env = _new_env(seed=request.seed, difficulty=request.difficulty)
    _force_problem(env, archetype=request.archetype, task_id=request.task_id, difficulty=request.difficulty)
    session_id = SESSIONS.put(env)
    return JSONResponse(content={"session_id": session_id, "state": _serialize_state(env)})


@app.post("/api/session/{session_id}/reset")
def reset_session(session_id: str, request: SessionCreateRequest) -> JSONResponse:
    env = _get_session_env(session_id)
    env._current_difficulty = request.difficulty
    _force_problem(env, archetype=request.archetype, task_id=request.task_id, difficulty=request.difficulty)
    return JSONResponse(content={"session_id": session_id, "state": _serialize_state(env)})


@app.get("/api/session/{session_id}")
def get_session(session_id: str) -> JSONResponse:
    env = _get_session_env(session_id)
    return JSONResponse(content={"session_id": session_id, "state": _serialize_state(env)})


@app.post("/api/session/{session_id}/run")
def run_session(session_id: str, request: SolverRunRequest) -> JSONResponse:
    env = _get_session_env(session_id)
    return JSONResponse(content=_run_episode(env, request))


@app.post("/api/benchmark")
def run_benchmark(request: BenchmarkRequest) -> JSONResponse:
    return JSONResponse(content=_benchmark(request))
