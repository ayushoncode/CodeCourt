import { useEffect, useState } from "react";
import {
  Activity,
  BadgeCheck,
  BarChart3,
  ChevronRight,
  CircleAlert,
  ClipboardList,
  Database,
  FlaskConical,
  Play,
  Server,
  TerminalSquare,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:7860";

const ARCHETYPES = ["array", "graph", "dp"];
const DIFFICULTIES = [1, 2, 3];

const pipelineSteps = [
  "Create a seeded adversarial episode from the OpenEnv backend.",
  "Collect solver completions and send them to the Docker Oracle sandbox.",
  "Score correctness, hidden-test robustness, and anti-gaming signals.",
  "Apply GRPO reward shaping to improve the Solver policy.",
  "Track artifacts and compare baseline vs. trained behavior.",
];

function classNames(...values) {
  return values.filter(Boolean).join(" ");
}

function formatPercent(value) {
  if (value == null || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}

function formatReward(value) {
  if (value == null || Number.isNaN(value)) return "n/a";
  return value.toFixed(2);
}

function Pill({ children, tone = "default" }) {
  const tones = {
    default: "border-slate-700 bg-slate-900/70 text-slate-300",
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    danger: "border-rose-500/30 bg-rose-500/10 text-rose-300",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-300",
    accent: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
  };

  return (
    <span
      className={classNames(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium tracking-wide",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}

function SectionCard({ icon: Icon, title, subtitle, children, action }) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 shadow-[0_0_0_1px_rgba(15,23,42,0.4),0_30px_80px_rgba(2,8,23,0.55)] backdrop-blur">
      <div className="flex items-start justify-between gap-4 border-b border-slate-800 px-6 py-5">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-300">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
            {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
          </div>
        </div>
        {action}
      </div>
      <div className="px-6 py-5">{children}</div>
    </section>
  );
}

function Header({ health }) {
  const healthy = health?.status === "ok";

  return (
    <header className="rounded-[2rem] border border-slate-800 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(244,114,182,0.14),_transparent_30%),rgba(2,6,23,0.92)] px-7 py-7 shadow-2xl">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-3xl">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <Pill tone="accent">CodeCourt OpenEnv Space</Pill>
            <Pill tone="default">v1.0.0</Pill>
            <Pill tone={healthy ? "success" : "danger"}>
              <Activity className="mr-2 h-3.5 w-3.5" />
              API {healthy ? "Healthy" : "Unavailable"}
            </Pill>
          </div>
          <h1 className="max-w-4xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            Adversarial RL arena for code generation, hidden failures, and judge-ready proof.
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 sm:text-base">
            CodeCourt visualizes the full OpenEnv loop: episode generation, secure code execution,
            GRPO reward shaping, and artifact tracking. This dashboard is designed to make failure,
            intervention, and improvement obvious in a single demo.
          </p>
        </div>

        <div className="grid min-w-[280px] gap-3 rounded-3xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase tracking-[0.2em] text-slate-500">Story Arc</span>
            <ChevronRight className="h-4 w-4 text-slate-600" />
          </div>
          <div className="grid gap-3">
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-3">
              <p className="text-xs uppercase tracking-[0.2em] text-rose-300">Before</p>
              <p className="mt-1 text-sm text-slate-200">
                Brute-force solvers fail on hidden adversarial cases.
              </p>
            </div>
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-3">
              <p className="text-xs uppercase tracking-[0.2em] text-amber-300">Fix</p>
              <p className="mt-1 text-sm text-slate-200">
                Reward shaping, sandboxed Oracle, and seeded task variation.
              </p>
            </div>
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-3">
              <p className="text-xs uppercase tracking-[0.2em] text-emerald-300">After</p>
              <p className="mt-1 text-sm text-slate-200">
                Better pass rate, stronger reward, clearer training evidence.
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function EnvironmentConsole({ onCreateEpisode, loading }) {
  const [archetype, setArchetype] = useState("array");
  const [difficulty, setDifficulty] = useState(1);

  return (
    <SectionCard
      icon={Server}
      title="Environment Console"
      subtitle="Configure the OpenEnv episode and create a fresh adversarial task."
    >
      <div className="grid gap-4 xl:grid-cols-2">
        <label className="grid gap-2 text-sm text-slate-300">
          Archetype
          <select
            value={archetype}
            onChange={(event) => setArchetype(event.target.value)}
            className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-500"
          >
            {ARCHETYPES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        <label className="grid gap-2 text-sm text-slate-300">
          Difficulty
          <select
            value={difficulty}
            onChange={(event) => setDifficulty(Number(event.target.value))}
            className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100 outline-none transition focus:border-cyan-500"
          >
            {DIFFICULTIES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => onCreateEpisode({ archetype, difficulty })}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-2xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Play className="h-4 w-4" />
          {loading ? "Creating..." : "Create Episode"}
        </button>
        <Pill tone="default">OpenEnv Session</Pill>
      </div>
    </SectionCard>
  );
}

function BenchmarkSandbox({ onRun, loading, benchmark }) {
  return (
    <SectionCard
      icon={BarChart3}
      title="Benchmark Sandbox"
      subtitle="Run baseline and reference behavior across fresh episodes."
      action={
        <button
          type="button"
          onClick={onRun}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-cyan-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          <FlaskConical className="h-4 w-4" />
          {loading ? "Running..." : "Run Benchmark"}
        </button>
      }
    >
      <div className="overflow-hidden rounded-2xl border border-slate-800">
        <table className="min-w-full divide-y divide-slate-800 text-sm">
          <thead className="bg-slate-900/80 text-left text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Episode</th>
              <th className="px-4 py-3 font-medium">Task</th>
              <th className="px-4 py-3 font-medium">Outcome</th>
              <th className="px-4 py-3 font-medium">Pass Rate</th>
              <th className="px-4 py-3 font-medium">Reward</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 bg-slate-950/40">
            {(benchmark?.episodes ?? []).length ? (
              benchmark.episodes.map((episode) => (
                <tr key={episode.episode} className="text-slate-200">
                  <td className="px-4 py-3">{episode.episode + 1}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium">{episode.archetype}</div>
                    <div className="text-xs text-slate-500">task {episode.task_id}</div>
                  </td>
                  <td className="px-4 py-3">
                    <Pill tone={episode.outcome === "solver_wins" ? "success" : "danger"}>
                      {episode.outcome}
                    </Pill>
                  </td>
                  <td className="px-4 py-3">{formatPercent(episode.solver_pass_rate)}</td>
                  <td className="px-4 py-3">{formatReward(episode.solver_reward)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-slate-500">
                  No benchmark run yet. Trigger the sandbox to compare baseline vs. reference behavior.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {benchmark?.summary ? (
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Avg Pass Rate</div>
            <div className="mt-2 text-2xl font-semibold text-white">
              {formatPercent(benchmark.summary.avg_solver_pass_rate)}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Avg Reward</div>
            <div className="mt-2 text-2xl font-semibold text-white">
              {formatReward(benchmark.summary.avg_solver_reward)}
            </div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Setter Win Rate</div>
            <div className="mt-2 text-2xl font-semibold text-white">
              {formatPercent(benchmark.summary.setter_win_rate)}
            </div>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}

function LiveExecutionArena({ session, lastRun }) {
  const resultTone =
    lastRun?.info?.outcome === "solver_wins"
      ? "text-emerald-300"
      : lastRun?.info?.outcome
        ? "text-rose-300"
        : "text-slate-500";

  return (
    <SectionCard
      icon={TerminalSquare}
      title="Live Execution Arena"
      subtitle="Terminal-style view of the current problem and latest solver result."
    >
      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-3xl border border-slate-800 bg-[#050816] p-4">
          <div className="mb-4 flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-rose-400" />
            <span className="h-3 w-3 rounded-full bg-amber-400" />
            <span className="h-3 w-3 rounded-full bg-emerald-400" />
            <span className="ml-3 text-xs uppercase tracking-[0.25em] text-slate-500">
              Current Problem
            </span>
          </div>
          <pre className="min-h-[280px] overflow-auto whitespace-pre-wrap rounded-2xl border border-slate-800 bg-slate-950 p-4 text-sm leading-7 text-slate-200">
            {session?.problem?.description ??
              "Create an episode to view the generated problem statement and hidden-test-ready task."}
          </pre>
        </div>

        <div className="rounded-3xl border border-slate-800 bg-[#050816] p-4">
          <div className="mb-4 flex items-center justify-between">
            <span className="text-xs uppercase tracking-[0.25em] text-slate-500">Run Results</span>
            <span className={classNames("text-sm font-semibold", resultTone)}>
              {lastRun?.info?.outcome ?? "No execution yet"}
            </span>
          </div>
          <div className="grid gap-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Pass Rate</div>
              <div className="mt-2 text-2xl font-semibold text-white">
                {formatPercent(lastRun?.info?.solver_pass_rate)}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Solver Reward</div>
              <div className="mt-2 text-2xl font-semibold text-white">
                {formatReward(lastRun?.solver_reward_info?.reward)}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Status</div>
              <div className="mt-2 flex flex-wrap gap-2">
                <Pill tone={lastRun?.info?.setter_valid ? "success" : "danger"}>
                  setter {lastRun?.info?.setter_valid ? "valid" : "invalid"}
                </Pill>
                <Pill tone="default">
                  hidden {formatPercent(lastRun?.info?.solver_hidden_pass_rate)}
                </Pill>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

function TrainingPipelineStatus() {
  return (
    <SectionCard
      icon={ClipboardList}
      title="Training Pipeline"
      subtitle="The 5-step GRPO loop visualized for demo clarity."
    >
      <div className="grid gap-3">
        {pipelineSteps.map((step, index) => (
          <div
            key={step}
            className="flex items-start gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-cyan-400 font-semibold text-slate-950">
              {index + 1}
            </div>
            <div>
              <p className="text-sm font-medium text-slate-100">{step}</p>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

function ArtifactTracker({ artifacts }) {
  const statusItems = [
    ["Baseline", artifacts?.baseline_available],
    ["Manifest", artifacts?.training_manifest_available],
    ["GRPO Logs", artifacts?.training_log_available],
    ["Plots", artifacts?.plots_available],
  ];

  return (
    <SectionCard
      icon={Database}
      title="Artifact Tracker"
      subtitle="Judge-facing evidence that the training loop is real and measurable."
    >
      <div className="flex flex-wrap gap-3">
        {statusItems.map(([label, present]) => (
          <Pill key={label} tone={present ? "success" : "danger"}>
            {present ? <BadgeCheck className="mr-2 h-3.5 w-3.5" /> : <CircleAlert className="mr-2 h-3.5 w-3.5" />}
            {label} {present ? "present" : "missing"}
          </Pill>
        ))}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Baseline Pass Rate</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {formatPercent(artifacts?.baseline_summary?.avg_solver_pass_rate)}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Latest Reward</div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {formatReward(artifacts?.latest_training_metrics?.reward)}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export default function CodeCourtDashboard() {
  const [health, setHealth] = useState(null);
  const [artifacts, setArtifacts] = useState(null);
  const [session, setSession] = useState(null);
  const [lastRun, setLastRun] = useState(null);
  const [benchmark, setBenchmark] = useState(null);
  const [creatingEpisode, setCreatingEpisode] = useState(false);
  const [runningBenchmark, setRunningBenchmark] = useState(false);

  useEffect(() => {
    async function bootstrap() {
      try {
        const [healthResponse, artifactsResponse] = await Promise.all([
          fetch(`${API_BASE}/api/health`).then((response) => response.json()),
          fetch(`${API_BASE}/api/artifacts`).then((response) => response.json()),
        ]);
        setHealth(healthResponse);
        setArtifacts(artifactsResponse);
      } catch (error) {
        setHealth({ status: "error", message: error.message });
      }
    }

    bootstrap();
  }, []);

  async function handleCreateEpisode({ archetype, difficulty }) {
    setCreatingEpisode(true);
    try {
      const response = await fetch(`${API_BASE}/api/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          archetype,
          difficulty,
          seed: 42,
        }),
      });
      const data = await response.json();
      setSession(data.state);
      setLastRun(null);
    } finally {
      setCreatingEpisode(false);
    }
  }

  async function handleRunBenchmark() {
    setRunningBenchmark(true);
    try {
      const response = await fetch(`${API_BASE}/api/benchmark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          episodes: 6,
          solver_mode: "brute_force",
          seed: 42,
        }),
      });
      const data = await response.json();
      setBenchmark(data);
    } finally {
      setRunningBenchmark(false);
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.12),_transparent_25%),radial-gradient(circle_at_top_right,_rgba(168,85,247,0.14),_transparent_30%),#020617] px-4 py-6 text-slate-100 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <Header health={health} />

        <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="grid gap-6">
            <EnvironmentConsole onCreateEpisode={handleCreateEpisode} loading={creatingEpisode} />
            <BenchmarkSandbox onRun={handleRunBenchmark} loading={runningBenchmark} benchmark={benchmark} />
          </div>

          <div className="grid gap-6">
            <LiveExecutionArena session={session} lastRun={lastRun} />
            <TrainingPipelineStatus />
            <ArtifactTracker artifacts={artifacts} />
          </div>
        </div>
      </div>
    </div>
  );
}
