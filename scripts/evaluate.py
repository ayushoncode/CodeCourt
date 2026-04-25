"""
Evaluation script — generates before/after comparison plots.
Run after training to produce the graphs for your README and presentation.

Usage:
    python scripts/evaluate.py \
        --baseline ./outputs/baseline_results.json \
        --trained  ./outputs/grpo_solver/training_log_history.json \
        --output   ./outputs/plots/
"""

import sys
import os
import json
import argparse
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def smooth(arr, window=10):
    result = []
    for i in range(len(arr)):
        start = max(0, i - window + 1)
        result.append(sum(arr[start:i+1]) / (i - start + 1))
    return result


def plot_reward_curves(history: list, output_dir: str):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.style as style
        style.use('dark_background')
    except ImportError:
        print("⚠ matplotlib not installed. pip install matplotlib")
        return

    if "episode" in history[0]:
        x_axis = [r["episode"] for r in history]
        setter_rewards = smooth([r["setter_reward"] for r in history])
        solver_rewards = smooth([r["solver_reward"] for r in history])
        pass_rates = smooth([r.get("solver_pass_rate", 0) for r in history])
        setter_elo = [r["setter_elo"] for r in history] if "setter_elo" in history[0] else None
        solver_elo = [r["solver_elo"] for r in history] if "solver_elo" in history[0] else None
        outcomes_source = history
        x_label = "Episode"
    else:
        log_records = [r for r in history if "step" in r and ("reward" in r or "reward_pass_rate" in r)]
        if not log_records:
            print("⚠ No plottable training metrics found")
            return
        x_axis = [r["step"] for r in log_records]
        setter_rewards = [0.0 for _ in log_records]
        solver_rewards = smooth([r.get("reward", 0.0) for r in log_records])
        pass_rates = smooth([r.get("reward_pass_rate", 0.0) for r in log_records])
        setter_elo = None
        solver_elo = None
        outcomes_source = []
        x_label = "Training Step"

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.patch.set_facecolor('#0d0d0d')
    fig.suptitle('CodeCourt — Training Metrics', color='white',
                 fontsize=16, fontweight='bold', y=0.98)

    COLORS = {
        'setter': '#ff6b35',
        'solver': '#4ecdc4',
        'grid': '#333333',
        'text': '#cccccc',
    }

    def style_ax(ax, title, xlabel, ylabel):
        ax.set_facecolor('#1a1a1a')
        ax.set_title(title, color='white', fontsize=11, pad=8)
        ax.set_xlabel(xlabel, color=COLORS['text'], fontsize=9)
        ax.set_ylabel(ylabel, color=COLORS['text'], fontsize=9)
        ax.tick_params(colors=COLORS['text'])
        ax.grid(True, color=COLORS['grid'], linewidth=0.5, alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color('#444444')

    # 1. Reward curves
    ax = axes[0, 0]
    if any(value != 0.0 for value in setter_rewards):
        ax.plot(x_axis, setter_rewards, color=COLORS['setter'],
                linewidth=1.5, label='Setter Reward')
    ax.plot(x_axis, solver_rewards, color=COLORS['solver'],
            linewidth=1.5, label='Solver Reward')
    ax.axhline(0, color='#555555', linewidth=0.8, linestyle='--')
    ax.legend(facecolor='#2a2a2a', edgecolor='#555555',
               labelcolor='white', fontsize=9)
    style_ax(ax, 'Reward Curves (smoothed, window=10)',
             x_label, 'Avg Reward')

    # 2. Solver pass rate over time
    ax = axes[0, 1]
    ax.plot(x_axis, [p * 100 for p in pass_rates],
            color=COLORS['solver'], linewidth=1.5)
    ax.set_ylim(0, 105)
    ax.axhline(50, color='#ffaa00', linewidth=0.8, linestyle='--',
               label='50% baseline')
    ax.legend(facecolor='#2a2a2a', edgecolor='#555555',
               labelcolor='white', fontsize=9)
    style_ax(ax, 'Solver Pass Rate (%)', x_label, 'Pass Rate %')

    # 3. Elo ratings
    ax = axes[1, 0]
    if setter_elo is not None and solver_elo is not None:
        ax.plot(x_axis, setter_elo, color=COLORS['setter'],
                linewidth=1.5, label='Setter Elo')
        ax.plot(x_axis, solver_elo, color=COLORS['solver'],
                linewidth=1.5, label='Solver Elo')
        ax.axhline(1000, color='#555555', linewidth=0.8, linestyle='--')
        ax.legend(facecolor='#2a2a2a', edgecolor='#555555',
                   labelcolor='white', fontsize=9)
        style_ax(ax, 'Elo Rating Progression', x_label, 'Elo Rating')
    else:
        ax.text(0.5, 0.5, 'GRPO run logs reward metrics,\nnot match Elo.',
                ha='center', va='center', color='white', fontsize=11)
        ax.set_axis_off()

    # 4. Outcome distribution (stacked bar, binned)
    ax = axes[1, 1]
    if not outcomes_source:
        ax.text(0.5, 0.5, 'Outcome bins are available for\nlegacy episode runs only.',
                ha='center', va='center', color='white', fontsize=11)
        ax.set_axis_off()
    else:
        bin_size = max(1, len(outcomes_source) // 20)
        bins = []
        setter_wins_pct = []
        solver_wins_pct = []
        invalid_pct = []

        for i in range(0, len(outcomes_source), bin_size):
            chunk = outcomes_source[i:i+bin_size]
            if not chunk:
                continue
            bins.append(i)
            outcomes = [r["outcome"] for r in chunk]
            n = len(outcomes)
            setter_wins_pct.append(outcomes.count("setter_wins") / n * 100)
            solver_wins_pct.append(outcomes.count("solver_wins") / n * 100)
            invalid_pct.append(outcomes.count("invalid") / n * 100)

        ax.bar(bins, setter_wins_pct, width=bin_size*0.8,
               color=COLORS['setter'], alpha=0.8, label='Setter Wins')
        ax.bar(bins, solver_wins_pct, width=bin_size*0.8,
               bottom=setter_wins_pct, color=COLORS['solver'],
               alpha=0.8, label='Solver Wins')
        ax.set_ylim(0, 105)
        ax.legend(facecolor='#2a2a2a', edgecolor='#555555',
                   labelcolor='white', fontsize=9)
        style_ax(ax, 'Outcome Distribution Over Time',
                 'Episode', 'Percentage %')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'training_curves.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"✓ Saved: {out_path}")
    plt.close()


def plot_before_after(baseline: dict, trained_history: list, output_dir: str):
    """Before/after comparison — the killer demo chart."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.style as style
        style.use('dark_background')
    except ImportError:
        return

    # Compute trained metrics (last 25% of training)
    if "episode" in trained_history[0]:
        n = len(trained_history)
        last_quarter = trained_history[n * 3 // 4:]
        trained_pass_rate = sum(
            r.get("solver_pass_rate", 0) for r in last_quarter
        ) / max(len(last_quarter), 1)
        trained_solver_reward = sum(r["solver_reward"] for r in last_quarter) / max(len(last_quarter), 1)
        trained_setter_win_rate = (
            sum(1 for r in last_quarter if r["outcome"] == "setter_wins")
            / max(len(last_quarter), 1) * 100
        )
    else:
        log_records = [r for r in trained_history if "step" in r and ("reward" in r or "reward_pass_rate" in r)]
        last_quarter = log_records[len(log_records) * 3 // 4:]
        trained_pass_rate = sum(
            r.get("reward_pass_rate", 0) for r in last_quarter
        ) / max(len(last_quarter), 1)
        trained_solver_reward = sum(r.get("reward", 0) for r in last_quarter) / max(len(last_quarter), 1)
        trained_setter_win_rate = 0.0

    baseline_summary = baseline.get("summary", baseline)
    baseline_pass = baseline_summary.get("avg_solver_pass_rate", 0.31)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.patch.set_facecolor('#0d0d0d')
    fig.suptitle('CodeCourt — Before vs After Training',
                 color='white', fontsize=15, fontweight='bold')

    BEFORE = '#ff6b35'
    AFTER = '#4ecdc4'
    BG = '#1a1a1a'

    metrics = [
        ("Solver Pass Rate", baseline_pass * 100, trained_pass_rate * 100, "%"),
        (
            "Avg Solver Reward",
            baseline_summary.get("avg_solver_reward", -15),
            trained_solver_reward,
            "pts",
        ),
        (
            "Setter Win Rate",
            baseline_summary.get("setter_win_rate", 0.4) * 100,
            trained_setter_win_rate,
            "%",
        ),
    ]

    for ax, (title, before_val, after_val, unit) in zip(axes, metrics):
        ax.set_facecolor(BG)
        bars = ax.bar(['Before\n(Untrained)', 'After\n(Trained)'],
                      [before_val, after_val],
                      color=[BEFORE, AFTER], width=0.5,
                      edgecolor='#333333')

        # Value labels
        for bar, val in zip(bars, [before_val, after_val]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + abs(before_val) * 0.05,
                    f"{val:.1f}{unit}",
                    ha='center', va='bottom', color='white',
                    fontsize=13, fontweight='bold')

        ax.set_title(title, color='white', fontsize=11, pad=10)
        ax.tick_params(colors='#cccccc')
        ax.set_ylabel(unit, color='#cccccc', fontsize=9)
        ax.grid(True, axis='y', color='#333333', linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_color('#444444')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_path = os.path.join(output_dir, 'before_after.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"✓ Saved: {out_path}")
    plt.close()


def build_evaluation_summary(baseline: dict | None, trained_history: list) -> dict:
    log_records = [row for row in trained_history if isinstance(row, dict) and "step" in row]
    final_record = log_records[-1] if log_records else {}
    baseline_summary = (baseline or {}).get("summary", baseline or {})
    baseline_pass = baseline_summary.get("avg_solver_pass_rate")
    trained_pass = final_record.get("reward_pass_rate")
    baseline_reward = baseline_summary.get("avg_solver_reward")
    trained_reward = final_record.get("reward")
    return {
        "baseline_pass_rate": baseline_pass,
        "trained_pass_rate": trained_pass,
        "pass_rate_delta": (trained_pass - baseline_pass) if baseline_pass is not None and trained_pass is not None else None,
        "baseline_reward": baseline_reward,
        "trained_reward": trained_reward,
        "reward_delta": (trained_reward - baseline_reward) if baseline_reward is not None and trained_reward is not None else None,
        "trained_robustness": final_record.get("reward_robustness"),
    }


def generate_reports(baseline_path: Path | None, trained_path: Path, output_dir: Path):
    trained = load_json(str(trained_path))
    history = trained if isinstance(trained, list) else trained.get("episodes", trained)
    os.makedirs(output_dir, exist_ok=True)
    plot_reward_curves(history, str(output_dir))

    baseline = None
    if baseline_path and baseline_path.exists():
        baseline = load_json(str(baseline_path))
        plot_before_after(baseline, history, str(output_dir))

    summary = build_evaluation_summary(baseline, history)
    with open(output_dir / "evaluation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved: {output_dir / 'evaluation_summary.json'}")
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", type=str,
                   default="./outputs/baseline_results.json")
    p.add_argument("--trained", type=str,
                   default="./outputs/grpo_solver/training_log_history.json")
    p.add_argument("--output", type=str, default="./outputs/plots/")
    args = p.parse_args()

    print("\n CodeCourt Evaluation")
    print("=" * 50)

    # Load data
    if not os.path.exists(args.trained):
        print(f"⚠ No training history at {args.trained}")
        print("  Run: python scripts/train.py --train-samples 54 --max-steps 30")
        return

    history = load_json(args.trained)
    history = history if isinstance(history, list) else history.get("episodes", history)
    print(f"Loaded {len(history)} training episodes")

    baseline_path = Path(args.baseline) if os.path.exists(args.baseline) else None
    if baseline_path is None:
        print(f"⚠ No baseline at {args.baseline} — before/after chart will be skipped")
        print("  Run: python scripts/baseline.py")

    generate_reports(baseline_path, Path(args.trained), Path(args.output))

    print(f"\n✓ All plots saved to: {args.output}")


if __name__ == "__main__":
    main()
