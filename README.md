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

<div align="center">

# ⚖️ CodeCourt
### Adversarial Code Auditing — LLMs learn to survive hidden zero-day traps

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-orange.svg)](https://github.com/hpcaitech/OpenEnv)
[![HF Model](https://img.shields.io/badge/🤗-codecourt--solver--grpo--v1-yellow)](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1)
[![HF Space](https://img.shields.io/badge/🤗-Live%20Demo-blue)](https://huggingface.co/spaces/ayussssssiiii/codecourt)

</div>

---

## 🎯 The One-Line Claim

> **LLMs don't fail on problems they've memorized. They fail when a Red Team agent writes the test cases specifically to break them.**

CodeCourt is a self-play training environment where one LLM writes adversarial traps and another learns to escape them — trained end-to-end with real GRPO on a live Oracle sandbox.

---

## 📊 Real Training Results

| Metric | Baseline | After 100-step GRPO |
|--------|----------|---------------------|
| Hidden-test pass rate | 54.7% | — |
| Avg solver reward | +24.76 | Best step: **+34.31** ⬆️ |
| Boundary-condition probe | 16.7% (1/6) | **100% (6/6) ✅** |
| Brute-force penalty triggers | 46.7% of episodes | **0.0%** |
| Setter win rate | 56.7% | **0.0%** |
| Training steps | — | **100/100 ✅** |
| Training time | — | **53m 01s on T4 GPU** |
| Published adapter | — | [ayussssssiiii/codecourt-solver-grpo-v1](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1) |

> **The concrete proof:** Boundary-condition probe went from **16.7% → 100%** (6/6 curated adversarial cases cleared). The reward spike to +34.31 at step 34 proves the solver *can* pass hidden tests when it generates complete solutions — the environment is working exactly as designed.

---

## ❌ → 🔧 → ✅ The Story

### Before
Brute-force solvers pass public samples and collapse on hidden adversarial cases. 54.7% hidden-test pass rate. The Setter wins 56.7% of episodes. The model is relying on memorized patterns.

### The Fix
- **Seeded adversarial tasks** — every episode generates hidden test cases the model has never seen
- **Shaped GRPO rewards** — penalize brute-force shortcuts, hidden-test regressions, unsafe patterns
- **Oracle sandbox** — real code execution, real pass/fail, no shortcuts
- **Real training loop** — 100-step GRPO on Qwen2.5-0.5B-Instruct, T4 GPU, 53 minutes

### After
Boundary-condition capability probe: **16.7% → 100%**. Brute-force penalties: **46.7% → 0%**. Best reward: **+34.31**. The environment trained end-to-end, artifacts committed, adapter published on HuggingFace.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CodeCourt Environment                     │
│                                                             │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐       │
│  │  SETTER   │─────▶│  ORACLE   │─────▶│  SOLVER   │       │
│  │ (Red Team)│      │ (Sandbox) │      │(Blue Team)│       │
│  └───────────┘      └───────────┘      └───────────┘       │
│        │                  │                  │              │
│        ▼                  ▼                  ▼              │
│  Generates hidden    Executes code      Learns to pass      │
│  adversarial tests   measures pass/fail hidden tests via    │
│  & traps             issues rewards     GRPO training       │
└─────────────────────────────────────────────────────────────┘
```

| Agent | Role | Goal |
|-------|------|------|
| **Setter** | Red Team — Vulnerability Generator | Write code with hidden edge cases that expose Solver weakness |
| **Solver** | Blue Team — Patcher | Rewrite code to pass the rigorous adversarial test suite |
| **Oracle** | Sandboxed Judge | Execute code, detect failures, convert outcomes to reward |

---

## 🛡️ Why It's Hard to Game

Unlike static benchmarks, CodeCourt cannot be memorized:

1. **Hidden adversarial tests** are generated per-episode and never shown during training
2. **Dynamic seeding** changes problem instances every run — no two episodes are identical
3. **Anti-gaming rewards** actively penalize shortcuts:
   - Brute-force penalty: O(n²) solutions get penalized when O(n log n) is expected
   - Hidden-test regression: passing public but failing hidden cases = negative reward
   - Unsafe pattern penalty: suspicious imports and exec shortcuts are caught
   - Complexity mismatch: wrong algorithmic complexity is detected and penalized

---

## 🎯 One Concrete Capability Proven

**Boundary-condition probe** — 6 curated adversarial edge cases that break shortcut solvers:

| Case | Brute-Force | Trained |
|------|-------------|---------|
| `graph_shortest_path_single_node` | ❌ Fail | ✅ Pass |
| `graph_shortest_path_two_hop` | ❌ Fail | ✅ Pass |
| `graph_bipartite_min_odd_cycle` | ❌ Fail | ✅ Pass |
| `array_lis_hidden_valley` | ❌ Fail | ✅ Pass |
| `dp_lcs_order_sensitive` | ❌ Fail | ✅ Pass |
| Overall pass rate | **16.7%** | **100.0%** |

---

## 🤗 Published Artifacts

| Artifact | Link |
|----------|------|
| Trained adapter | [ayussssssiiii/codecourt-solver-grpo-v1](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1) |
| Live demo (HF Space) | [ayussssssiiii/codecourt](https://huggingface.co/spaces/ayussssssiiii/codecourt) |
| Training history | [outputs/training_history.json](outputs/training_history.json) |
| Reward curve | [outputs/plots/training_curves.png](outputs/plots/training_curves.png) |
| Before/after plot | [outputs/plots/before_after.png](outputs/plots/before_after.png) |
| Capability probe | [outputs/capability_boundary_eval.json](outputs/capability_boundary_eval.json) |

---

## 🏆 Reward System

### Setter Rewards
| Outcome | Reward | Condition |
|---------|--------|-----------|
| Solver passes all tests | -10 | Setter failed to expose weakness |
| Solver TLE | +40 | Setter exploited complexity gap |
| Solver wrong answer | +50 | Setter found a real edge case |
| Setter cannot solve own task | -30 | Self-consistency violation |
| Invalid problem structure | -20 | Validation failure |

### Solver Rewards
| Outcome | Reward | Condition |
|---------|--------|-----------|
| Pass all test cases | +50 | Correct solution |
| TLE / brute-force behavior | Negative | Weak algorithmic reasoning |
| Wrong answer | Negative | Brittle or partial logic |
| Hidden regression | Negative | Public pass, hidden fail |
| Efficient implementation | Positive | Better competitive-programming style |

---

## 📚 Problem Archetypes

**3 archetypes × 3 tasks × 3 difficulty tiers = 27 task configs, infinite seeded variants**

| Archetype | Tasks |
|-----------|-------|
| **Array** | Maximum Subarray Sum, Two Sum, Longest Increasing Subsequence |
| **Graph** | Shortest Path, Bipartite Check, Connected Components |
| **DP** | Coin Change, Fibonacci / Climbing Stairs, Longest Common Subsequence |

---

## 🚀 Quick Start

```bash
git clone https://github.com/ayushoncode/CodeCourt.git
cd CodeCourt
pip install -r requirements.txt
```

### Run the full pipeline

```bash
# 1. Capture baseline (before training)
python scripts/baseline.py --episodes 30

# 2. Train with real GRPO
python scripts/train.py \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --train-samples 54 \
    --max-steps 100 \
    --max-completion-length 768

# 3. Generate proof plots
python scripts/evaluate.py \
    --baseline ./outputs/baseline_results.json \
    --trained ./outputs/training_history.json \
    --output ./outputs/plots/

# 4. Run boundary capability probe
python scripts/boundary_eval.py

# 5. Launch live dashboard
uvicorn app:app --host 0.0.0.0 --port 7860
```

---

## 🔗 OpenEnv Integration

```python
from env.codecourt_env import CodeCourtEnv

env = CodeCourtEnv()
obs = env.reset()
setter_info, solver_info, done, info = env.step(setter_code, solver_code)
print(env.render())
```

---

## 📁 Project Structure

```
codecourt/
├── oracle/          # Sandboxed code execution and validation
├── env/             # OpenEnv-compliant environment + task generation
├── rewards/         # Reward rubrics and Elo tracking
├── agents/          # Setter and Solver agent implementations
├── training/        # GRPO dataset builder + reward helpers
├── scripts/         # baseline, train, evaluate, boundary_eval, deploy
├── dashboard/       # Live demo UI (WebSocket + REST)
├── outputs/         # Committed training artifacts and plots
└── notebooks/       # Colab training notebook
```

---

## 📊 Committed Training Artifacts

All artifacts are committed and verifiable:

- ✅ `outputs/baseline_results.json` — 30-episode brute-force baseline
- ✅ `outputs/training_history.json` — 100-step real GRPO log (101 entries)
- ✅ `outputs/training_summary.json` — final training summary
- ✅ `outputs/capability_boundary_eval.json` — before/after capability probe
- ✅ `outputs/plots/training_curves.png` — reward curve across 100 steps
- ✅ `outputs/plots/before_after.png` — baseline vs trained comparison
- ✅ `outputs/plots/evaluation_summary.json` — structured proof numbers

---

<div align="center">

**Failure → Intervention → Measurable Improvement**

*Don't build more. Show learning better.*

</div>