---
title: CodeCourt
emoji: ⚖️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# ⚖ CodeCourt

LLMs do not usually fail on the problems they have already memorized. They fail when hidden edge cases and vulnerabilities expose brittle reasoning. CodeCourt isn't just generating synthetic data; it's an Adversarial Code Auditing Environment where AI agents learn to attack and defend software infrastructure through self-play.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.10+-green.svg)
![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-orange.svg)

## 🎯 The Story

Most coding benchmarks are static. Public tasks are visible, patterns repeat, and models can look strong through memorization. But infrastructure isn't static. Real coding robustness appears when:

- test cases are hidden
- edge cases are adversarial and resemble zero-day exploits
- brute-force shortcuts stop working

CodeCourt turns that into the training loop itself. We frame this as an automated vulnerability generation and patching pipeline:

| Agent | Role | Goal |
|-------|------|------|
| **Setter** | Red Team Vulnerability Generator | Write code with hidden edge cases, memory leaks, or logical bugs that expose solver weakness |
| **Solver** | Blue Team Patcher | Rewrite the code to pass the rigorous, adversarial test suite |
| **Oracle** | Sandboxed Judge | Execute code, detect failures, and convert outcomes into reward |

This is the core claim: **LLMs fail not on known problems, but when exposed to adversarial hidden edge cases. We built an environment where Red Team agents actively create those failures, forcing Blue Team agents to develop zero-day patching capabilities.**

## ❌ Failure → 🔧 Fix → ✅ Result

### Before

- Brute-force solvers can pass public samples and still fail hidden tests.
- Static problem sets are easy to overfit.
- Pure pass/fail rewards hide whether a model is actually getting more robust.

### Fix

- Added **seeded dynamic task variation** and adversarial hidden cases.
- Added **reward shaping** for correctness, hidden-test regression, fast I/O, and likely brute-force behavior.
- Added **training artifacts**: baseline, summaries, manifests, reward curves, and before-vs-after plots.

### Result

- CodeCourt is no longer just a benchmark runner.
- It now supports a judge-friendly learning story: weak baseline, targeted fixes, measurable improvement.
- The demo can show where the Solver fails, how training penalizes those failures, and how metrics improve afterward.

## 🏗 Architecture

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SETTER    │────▶│   ORACLE    │────▶│   SOLVER    │
│  (LLM Agent)│     │ (Executor)  │     │  (LLM Agent)│
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  Generates          Validates &          Writes Code
  Problems           Executes Code        Solutions
```

## 🛡️ Why It Is Hard To Hack

Most coding benchmarks are memorized. CodeCourt is harder to game because:

1. **Hidden adversarial tests** are separate from public examples.
2. **Dynamic task variation** changes instances by seed, reducing simple memorization.
3. **Anti-gaming rewards** penalize brute-force strategies, hidden-test regressions, and unsafe execution patterns.

## 🏆 Anti-Gaming Logic

- **Brute-force penalty**: likely high-complexity implementations are penalized when the task expects something sharper.
- **Hidden-test regression penalty**: passing public tests but failing hidden cases loses reward.
- **Repeated weak strategy pressure**: brittle control-flow patterns are discouraged across adversarial variants.
- **Unsafe pattern penalty**: suspicious imports and execution shortcuts are penalized.
- **Fast competitive-style implementation bonus**: efficient I/O and cleaner structure can gain reward.

## 📚 Problem Archetypes

CodeCourt includes **3 archetypes × 3 tasks × 3 difficulty tiers**:

### Array
- Maximum Subarray Sum
- Two Sum
- Longest Increasing Subsequence

### Graph
- Shortest Path
- Bipartite Check
- Connected Components

### Dynamic Programming
- Coin Change
- Fibonacci / Climbing Stairs
- Longest Common Subsequence

Each task can produce seeded variants and adversarial hidden cases.

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/codecourt.git
cd codecourt
pip install -r requirements.txt
```

For GPU training environments:

```bash
pip install -r requirements-training.txt
```

### Hugging Face Auth

```bash
cp .env.example .env
```

Set `HF_TOKEN` and `HF_SPACE_ID` in `.env`, then either:

```bash
huggingface-cli login
```

or rely on environment variables loaded from `.env`.

### 1. Capture Failure First

```bash
python scripts/baseline.py --episodes 50
```

This is your **before training** snapshot:

- weak solver
- low reward
- lower pass rate

### 2. Run Actual Training

```bash
python scripts/train.py \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --train-samples 54 \
    --max-steps 30
```

This performs real GRPO optimization using the Oracle sandbox as the reward source.

### 3. Generate Training Proof

```bash
python scripts/evaluate.py \
    --baseline ./outputs/baseline_results.json \
    --trained ./outputs/grpo_solver/training_log_history.json \
    --output ./outputs/plots/
```

This generates:

- `training_curves.png`
- `before_after.png`
- `evaluation_summary.json`

### 4. Launch the Demo

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then open `http://127.0.0.1:7860`.

### 5. Deploy to Hugging Face Spaces

```bash
python scripts/deploy_space.py --space-id your-username/codecourt
```

## 📊 Training Proof

CodeCourt is designed to produce explicit evidence of improvement:

1. `baseline_results.json` captures the weak starting policy.
2. `training_log_history.json` tracks reward and pass rate over GRPO steps.
3. `training_summary.json` summarizes the final training state.
4. `evaluation_summary.json` compares baseline vs trained behavior.
5. Plot artifacts visualize reward curves and before-vs-after gains.

## 📈 What To Show In The Demo

### Before Training

- brute solver fails on hidden cases
- solver reward is low
- pass rate is weak

### Fix

- reward shaping
- adversarial hidden tests
- dynamic problem variation

### After Training

- higher pass rate
- higher reward
- stronger robustness against hidden cases

That is the winning story: **failure, intervention, measurable improvement**.

## 🏆 Reward System

### Setter Rewards

| Outcome | Reward | Condition |
|---------|--------|-----------|
| Solver passes all tests | -10 | Setter failed to expose weakness |
| Solver TLE | +40 | Setter exploited complexity gap |
| Solver wrong answer | +50 | Setter found an edge case |
| Setter cannot solve own task | -30 | Self-consistency violation |
| Invalid problem structure | -20 | Validation failure |

### Solver Rewards

| Outcome | Reward | Condition |
|---------|--------|-----------|
| Pass all test cases | +50 | Correct solution |
| TLE / brute-force behavior | Negative | Weak algorithmic reasoning |
| Wrong answer | Negative | Brittle or partial logic |
| Hidden regression | Negative | Public pass, hidden fail |
| Efficient implementation traits | Positive | Better competitive-programming behavior |

## 📁 Project Structure

```text
codecourt/
├── oracle/            # Sandboxed execution and validation
├── env/               # OpenEnv environment and task generation
├── rewards/           # Reward rubrics and Elo tracking
├── agents/            # Setter and Solver agents
├── training/          # GRPO dataset + reward helpers
├── scripts/           # Baseline, training, evaluation, deploy
├── dashboard/         # Demo UI
├── notebooks/         # Colab notebook
└── tests/             # Oracle and environment tests
```

## 🔧 Key Config

| Argument | Default | Description |
|----------|---------|-------------|
| `--model` | Qwen/Qwen2.5-0.5B-Instruct | Base model to train |
| `--train-samples` | 54 | Number of prompts in GRPO dataset |
| `--max-steps` | 30 | GRPO optimization steps |
| `--num-generations` | 4 | Completions sampled per prompt |
| `--output-dir` | `./outputs/grpo_solver` | Training artifact directory |
| `--plots-dir` | `./outputs/plots` | Evaluation plot directory |

## 🔗 OpenEnv Integration

CodeCourt is compatible with the [OpenEnv](https://github.com/hpcaitech/OpenEnv) specification:

```python
from env.codecourt_env import CodeCourtEnv

env = CodeCourtEnv()
obs = env.reset()
setter_info, solver_info, done, info = env.step(setter_code, solver_code)
print(env.render())
```

## One-Line Advice

**Don’t build more. Show learning better.**
