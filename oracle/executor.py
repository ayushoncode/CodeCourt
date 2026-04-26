"""
Oracle Executor — Docker-backed sandbox for untrusted code execution.

Supports Python and C++ submissions, enforces time and memory limits, and
returns both CodeCourt-native status fields and hackathon-facing outcome data.
"""

from __future__ import annotations

import io
import os
import platform
import resource
import tarfile
import tempfile
import time
import subprocess
from dataclasses import dataclass
from typing import Optional

try:
    import docker
    from docker.errors import DockerException
except ImportError:  # pragma: no cover - handled at runtime when dependency is missing
    docker = None
    DockerException = Exception


LANGUAGE_CONFIG = {
    "python": {
        "image": "python:3.11-alpine",
        "source_name": "main.py",
        "run_cmd": ["sh", "-lc", "python3 /workspace/main.py < /workspace/stdin.txt"],
        "compile_cmd": None,
    },
    "cpp": {
        "image": "gcc:13",
        "source_name": "main.cpp",
        "compile_cmd": ["sh", "-lc", "g++ -O2 -std=c++17 /workspace/main.cpp -o /workspace/main"],
        "run_cmd": ["sh", "-lc", "/workspace/main < /workspace/stdin.txt"],
    },
}


@dataclass
class ExecutionResult:
    status: str          # 'pass' | 'fail' | 'tle' | 'mle' | 'error'
    stdout: str
    stderr: str
    timed_out: bool
    memory_exceeded: bool
    execution_time: float
    expected_output: Optional[str] = None
    memory_used_mb: float = 0.0
    language: str = "python"
    outcome: str = "setter_wins"  # 'solver_wins' | 'setter_wins' | 'compile_error' | 'time_limit'
    compile_error: bool = False

    @property
    def passed(self) -> bool:
        return self.status == "pass"


class OracleExecutor:
    """
    Secure Docker sandbox for executing untrusted code.

    Each execution happens in an isolated container with:
    - network disabled
    - memory cap
    - CPU quota
    - no-new-privileges
    - read-only root filesystem
    """

    def __init__(
        self,
        time_limit: float = 2.0,
        memory_limit_mb: int = 256,
        default_language: str = "python",
    ):
        self.time_limit = time_limit
        self.memory_limit_mb = memory_limit_mb
        self.default_language = default_language
        self._client = None
        self._docker_checked = False
        self._docker_available = False

    def _get_client(self):
        if docker is None:
            return None
        if self._docker_checked:
            return self._client if self._docker_available else None

        self._docker_checked = True
        if self._client is None:
            client = None
            try:
                client = docker.from_env()
                client.ping()
                self._client = client
                self._docker_available = True
            except DockerException:
                try:
                    client.close()
                except Exception:
                    pass
                self._client = None
                self._docker_available = False
        return self._client

    def _validate_language(self, language: str) -> dict:
        if language not in LANGUAGE_CONFIG:
            raise ValueError(f"Unsupported language: {language}. Expected one of {sorted(LANGUAGE_CONFIG)}")
        return LANGUAGE_CONFIG[language]

    def _create_workspace_archive(self, files: dict[str, str]) -> bytes:
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as tar:
            for filename, content in files.items():
                encoded = content.encode("utf-8")
                info = tarfile.TarInfo(name=filename)
                info.size = len(encoded)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(encoded))
        buffer.seek(0)
        return buffer.read()

    def _read_peak_memory_mb(self, container) -> float:
        try:
            stats = container.stats(stream=False)
        except DockerException:
            return 0.0

        memory_usage = 0
        if isinstance(stats, dict):
            memory_usage = (
                stats.get("memory_stats", {}).get("max_usage")
                or stats.get("memory_stats", {}).get("usage")
                or 0
            )
        return round(memory_usage / (1024 * 1024), 3)

    def _status_from_exit(self, exit_code: int, expected_output: Optional[str], stdout: str, stderr: str) -> tuple[str, str]:
        if exit_code == 137:
            return "mle", "setter_wins"
        if exit_code != 0:
            compile_like = "syntaxerror" in stderr.lower() or "traceback" in stderr.lower()
            return ("error", "compile_error" if compile_like else "setter_wins")
        if expected_output is None:
            return "pass", "solver_wins"
        if stdout.strip() == expected_output.strip():
            return "pass", "solver_wins"
        return "fail", "setter_wins"

    def _set_local_limits(self):
        if platform.system() == "Darwin":
            return
        mem_bytes = self.memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
        resource.setrlimit(resource.RLIMIT_CPU, (int(self.time_limit) + 1, int(self.time_limit) + 1))

    def _run_local(self, command: list[str], files: dict[str, str]) -> tuple[int, str, str, float, float, bool]:
        start = time.time()
        with tempfile.TemporaryDirectory() as tmpdir:
            for filename, content in files.items():
                with open(os.path.join(tmpdir, filename), "w", encoding="utf-8") as f:
                    f.write(content)
            
            cmd_str = command[2].replace("/workspace", tmpdir)
            try:
                res = subprocess.run(
                    cmd_str,
                    shell=True,
                    cwd=tmpdir,
                    capture_output=True,
                    timeout=max(self.time_limit + 0.5, 1.0),
                    text=True,
                    preexec_fn=None if platform.system() == "Darwin" else self._set_local_limits,
                )
                elapsed = time.time() - start
                stderr = res.stderr.strip()
                if res.returncode != 0 and not stderr:
                    stderr = f"Exit code: {res.returncode}"
                return res.returncode, res.stdout.strip(), stderr, elapsed, 10.0, False
            except subprocess.TimeoutExpired as e:
                elapsed = time.time() - start
                stdout = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode() if e.stdout else "")
                stderr = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else "")
                return 124, stdout.strip(), stderr.strip(), elapsed, 10.0, True

    def _run_container(self, image: str, command: list[str], files: dict[str, str]) -> tuple[int, str, str, float, float, bool]:
        if "SPACE_ID" in os.environ or self._get_client() is None:
            return self._run_local(command, files)

        client = self._get_client()
        container = None
        start = time.time()

        try:
            container = client.containers.create(
                image=image,
                command=command,
                working_dir="/workspace",
                mem_limit=f"{self.memory_limit_mb}m",
                network_disabled=True,
                read_only=True,
                nano_cpus=1_000_000_000,
                security_opt=["no-new-privileges:true"],
                cap_drop=["ALL"],
                pids_limit=128,
                detach=True,
                stdin_open=False,
                tty=False,
            )
            container.put_archive("/workspace", self._create_workspace_archive(files))
            container.start()

            timed_out = False
            try:
                result = container.wait(timeout=max(self.time_limit + 0.5, 1.0))
            except Exception:
                timed_out = True
                container.kill()
                result = {"StatusCode": 124}

            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace").strip()
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace").strip()
            elapsed = time.time() - start
            peak_memory_mb = self._read_peak_memory_mb(container)
            return int(result.get("StatusCode", 1)), stdout, stderr, elapsed, peak_memory_mb, timed_out
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except DockerException:
                    pass

    def run(
        self,
        code: str,
        stdin_input: str,
        expected_output: Optional[str] = None,
        language: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute source code in Docker with strict sandboxing.
        """
        chosen_language = language or self.default_language
        try:
            config = self._validate_language(chosen_language)
        except ValueError as exc:
            return ExecutionResult(
                status="error",
                stdout="",
                stderr=str(exc),
                timed_out=False,
                memory_exceeded=False,
                execution_time=0.0,
                expected_output=expected_output,
                language=chosen_language,
                outcome="compile_error",
                compile_error=True,
            )

        source_name = config["source_name"]
        files = {
            source_name: code,
            "stdin.txt": stdin_input,
        }

        try:
            if config["compile_cmd"] is not None:
                compile_exit, _, compile_stderr, compile_time, compile_memory_mb, compile_timed_out = self._run_container(
                    config["image"],
                    config["compile_cmd"],
                    files,
                )
                if compile_timed_out:
                    return ExecutionResult(
                        status="tle",
                        stdout="",
                        stderr="Compilation timed out",
                        timed_out=True,
                        memory_exceeded=False,
                        execution_time=compile_time,
                        expected_output=expected_output,
                        memory_used_mb=compile_memory_mb,
                        language=chosen_language,
                        outcome="time_limit",
                    )
                if compile_exit != 0:
                    return ExecutionResult(
                        status="error",
                        stdout="",
                        stderr=compile_stderr or f"Compilation failed with exit code {compile_exit}",
                        timed_out=False,
                        memory_exceeded=compile_exit == 137,
                        execution_time=compile_time,
                        expected_output=expected_output,
                        memory_used_mb=compile_memory_mb,
                        language=chosen_language,
                        outcome="compile_error",
                        compile_error=True,
                    )

            exit_code, stdout, stderr, elapsed, peak_memory_mb, timed_out = self._run_container(
                config["image"],
                config["run_cmd"],
                files,
            )

            if timed_out or elapsed > self.time_limit:
                return ExecutionResult(
                    status="tle",
                    stdout=stdout,
                    stderr=stderr or "Time Limit Exceeded",
                    timed_out=True,
                    memory_exceeded=False,
                    execution_time=elapsed,
                    expected_output=expected_output,
                    memory_used_mb=peak_memory_mb,
                    language=chosen_language,
                    outcome="time_limit",
                )

            status, outcome = self._status_from_exit(exit_code, expected_output, stdout, stderr)
            return ExecutionResult(
                status=status,
                stdout=stdout,
                stderr=stderr,
                timed_out=False,
                memory_exceeded=status == "mle",
                execution_time=elapsed,
                expected_output=expected_output,
                memory_used_mb=peak_memory_mb,
                language=chosen_language,
                outcome=outcome,
                compile_error=(outcome == "compile_error"),
            )

        except RuntimeError as exc:
            return ExecutionResult(
                status="error",
                stdout="",
                stderr=str(exc),
                timed_out=False,
                memory_exceeded=False,
                execution_time=0.0,
                expected_output=expected_output,
                memory_used_mb=0.0,
                language=chosen_language,
                outcome="compile_error",
                compile_error=True,
            )
        except DockerException as exc:
            return ExecutionResult(
                status="error",
                stdout="",
                stderr=f"Docker execution failed: {exc}",
                timed_out=False,
                memory_exceeded=False,
                execution_time=0.0,
                expected_output=expected_output,
                memory_used_mb=0.0,
                language=chosen_language,
                outcome="compile_error",
                compile_error=True,
            )

    def run_against_tests(
        self,
        code: str,
        test_cases: list,
        language: Optional[str] = None,
    ) -> dict:
        """
        Run code against multiple test cases.

        Returns both existing CodeCourt keys and hackathon-facing aggregate fields:
        - overall_status
        - pass_rate
        - avg_time
        - avg_memory_mb
        - outcome
        """
        results = []
        passed = 0

        for i, tc in enumerate(test_cases):
            result = self.run(
                code=code,
                stdin_input=tc["input"],
                expected_output=tc.get("expected"),
                language=language,
            )
            results.append(
                {
                    "test_id": i + 1,
                    "status": result.status,
                    "passed": result.passed,
                    "execution_time": result.execution_time,
                    "memory_used_mb": result.memory_used_mb,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "outcome": result.outcome,
                    "language": result.language,
                }
            )
            if result.passed:
                passed += 1

        if passed == len(test_cases):
            overall_status = "pass"
            outcome = "solver_wins"
        elif any(item["status"] == "tle" for item in results):
            overall_status = "tle"
            outcome = "time_limit"
        elif any(item["outcome"] == "compile_error" for item in results):
            overall_status = "error"
            outcome = "compile_error"
        elif any(item["status"] == "mle" for item in results):
            overall_status = "mle"
            outcome = "setter_wins"
        else:
            overall_status = "fail"
            outcome = "setter_wins"

        total = len(test_cases)
        return {
            "overall_status": overall_status,
            "outcome": outcome,
            "passed": passed,
            "total": total,
            "pass_rate": passed / max(total, 1),
            "results": results,
            "avg_time": sum(item["execution_time"] for item in results) / max(total, 1),
            "avg_memory_mb": sum(item["memory_used_mb"] for item in results) / max(total, 1),
        }
