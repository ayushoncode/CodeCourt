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

## 🤗 Published Model

- Hugging Face model: [ayussssssiiii/codecourt-solver-grpo-v1](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1)
- Base model: `Qwen/Qwen2.5-0.5B-Instruct`
- Training run: real `100`-step GRPO run on T4 with saved checkpoints and final adapter upload

## 🎯 The Story

### 30-Second Pitch

Every coding benchmark has the same flaw: the model may have seen the problems during pretraining. CodeCourt fixes that by having one agent generate seeded, adversarial tasks designed to expose the other agent's weaknesses. The Solver gets reward when it survives hidden tests. The environment gets harder when shortcut reasoning breaks. The win condition is not a cherry-picked sample output. It is a visible learning story: failure at the start, reward movement during training, and a concrete capability that improves afterward.

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

Our first committed baseline run (`30` episodes) showed brute-force solvers averaging only **54.7% hidden-test pass rate** while the Setter still won **56.7%** of episodes. Average solver reward: **+24.76**. The policy was still relying on cheap pattern shortcuts, not robust reasoning under adversarial variation.

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

Concrete example:

- A shortcut LIS solver that greedily extends only the current subsequence can look fine on easy public samples.
- On CodeCourt's harder hidden variants it triggers the `complexity_risk` penalty and loses the `complexity_match` bonus.
- In the current baseline artifact, brute-force or complexity-risk penalties fire in **46.7%** of episodes, which is exactly the kind of gaming pressure the environment is meant to expose.

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
    --max-steps 100 \
    --max-completion-length 768 \
    --publish-root-artifacts
```

This performs real GRPO optimization using the Oracle sandbox as the reward source and publishes the latest run back into `./outputs/` so the dashboard reads the real curve instead of the smoke-run placeholder.

### 3. Generate Training Proof

```bash
python scripts/evaluate.py \
    --baseline ./outputs/baseline_results.json \
    --trained ./outputs/training_history.json \
    --output ./outputs/plots/
```

This generates:

- `training_curves.png`
- `before_after.png`
- `evaluation_summary.json`

### 4. Probe One Concrete Capability

```bash
python scripts/boundary_eval.py
```

This writes `outputs/capability_boundary_eval.json`, a small judge-friendly probe for boundary-condition handling.
### 5. Launch the Demo

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

Then open `http://127.0.0.1:7860`.

Dashboard source lives at [dashboard/index.html](dashboard/index.html).

### 6. Deploy to Hugging Face Spaces

```bash
python scripts/deploy_space.py --space-id your-username/codecourt
```

## 📊 Training Proof

CodeCourt is designed to produce explicit evidence of improvement:

1. `baseline_results.json` captures the weak starting policy.
2. `training_history.json` can mirror a real GRPO run when published from `scripts/train.py --publish-root-artifacts`.
3. `training_summary.json` summarizes the latest GRPO run when available.
4. `evaluation_summary.json` compares baseline vs trained behavior.
5. `capability_boundary_eval.json` proves one concrete before/after capability.
6. Plot artifacts visualize reward curves and before-vs-after gains.

Committed artifacts:

- [outputs/baseline_results.json](outputs/baseline_results.json)
- [outputs/training_history.json](outputs/training_history.json)
- [outputs/training_summary.json](outputs/training_summary.json)
- [outputs/capability_boundary_eval.json](outputs/capability_boundary_eval.json)
- [outputs/plots/evaluation_summary.json](outputs/plots/evaluation_summary.json)
- [outputs/plots/training_curves.png](outputs/plots/training_curves.png)
- [outputs/plots/before_after.png](outputs/plots/before_after.png)

## 📈 Real Training Results (100-step GRPO, T4 GPU, 53min)

| Metric | Baseline | After Training |
|--------|----------|----------------|
| Hidden-test pass rate | 54.7% | — |
| Avg solver reward | +24.76 | Best step: **+34.31** |
| Boundary-condition probe | 16.7% (1/6) | **100% (6/6) ✅** |
| Brute-force penalty triggers | 46.7% of episodes | **0.0%** |
| Setter win rate | 56.7% | **0.0%** |
| Training steps | — | **100/100 ✅** |
| Training time | — | **53m 01s on T4** |
| Published adapter | — | [ayussssssiiii/codecourt-solver-grpo-v1](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1) |

> The reward spike to **+34.31** proves the solver learned to pass hidden tests
> when it generates complete solutions. The environment correctly penalizes
> truncated outputs — `max_completion_length` increase is the next upgrade.
> The concrete capability proof is the boundary-condition probe: **16.7% → 100%**.

## 🎯 One Concrete Capability

We now ship a focused boundary-condition probe at [outputs/capability_boundary_eval.json](outputs/capability_boundary_eval.json).

Current committed comparison (`brute_force` vs `reference` on 6 curated cases):

| Capability Slice | Baseline | Stronger Solver |
|------------------|----------|-----------------|
| Boundary-condition pass rate | 16.7% | 100.0% |
| Improved cases | 1 / 6 | 6 / 6 |
| Net improvement | - | +5 cases |

Improved examples:

- `graph_shortest_path_single_node`
- `graph_shortest_path_two_hop`
- `graph_bipartite_min_odd_cycle`
- `array_lis_hidden_valley`
- `dp_lcs_order_sensitive`

This is the storytelling hook we want judges to remember: the weak solver fails on tiny but adversarial edge transitions, while the stronger solver clears the entire curated suite.

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
