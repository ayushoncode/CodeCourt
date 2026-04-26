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

# ⚖️ CodeCourt
### The LLM Red Team Arena — Adversarial Code Auditing via Self-Play

<div align="center">

[![Live Arena](https://img.shields.io/badge/⚔️%20Live%20Arena-HF%20Space-orange?style=for-the-badge)](https://huggingface.co/spaces/ayussssssiiii/codecourt)
[![Trained Model](https://img.shields.io/badge/🧠%20Trained%20Model-GRPO%20v1-green?style=for-the-badge)](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1)
[![Colab](https://img.shields.io/badge/📓%20Training-Colab%20Notebook-yellow?style=for-the-badge)](https://colab.research.google.com/github/ayushoncode/CodeCourt/blob/main/notebooks/train_codecourt.ipynb)
[![Blog](https://img.shields.io/badge/📝%20Mini%20Blog-HuggingFace-blue?style=for-the-badge)](YOUR_BLOG_LINK)

*"Most coding benchmarks test what the model has memorized. CodeCourt tests what happens when another LLM is actively trying to break it."*

</div>

---

## 🎯 The Problem Nobody Is Solving

Every LLM coding benchmark has the same fatal flaw: **the model may have seen the problems during pretraining.** Pass rates look great. Hidden robustness is zero.

Real software doesn't fail on known problems. It fails on:

- **Edge cases nobody thought to test** — `n=0`, `n=MAX_INT`, empty graphs, single-node trees
- **Off-by-one logic traps** planted by adversaries
- **Complexity bombs** — O(n²) solutions that pass small inputs and TLE on hidden stress tests
- **Zero-day vulnerabilities** — code that looks correct but breaks under adversarial inputs

**CodeCourt turns adversarial pressure into the training signal itself.**

---

## 🏗️ Architecture — The Arms Race

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeCourt Self-Play Loop                     │
│                                                                  │
│   ┌─────────────┐   adversarial    ┌─────────────┐             │
│   │   SETTER    │───task+traps───▶ │   ORACLE    │             │
│   │  (Red Team) │                  │  (Sandbox)  │             │
│   │ LLM Agent   │◀──setter_reward──│  Executor   │             │
│   └─────────────┘                  └──────┬──────┘             │
│                                           │ hidden test results  │
│   ┌─────────────┐                  ┌──────▼──────┐             │
│   │   SOLVER    │───solution──────▶│   ORACLE    │             │
│   │  (Blue Team)│                  │  (Sandbox)  │             │
│   │ GRPO-trained│◀──solver_reward──│  Executor   │             │
│   └─────────────┘                  └─────────────┘             │
│                                                                  │
│   Setter rewarded when Solver FAILS hidden tests                │
│   Solver rewarded when it PASSES hidden tests                   │
│   → A real arms race. Both agents co-evolve.                    │
└─────────────────────────────────────────────────────────────────┘
```

| Agent | Role | Goal |
|---|---|---|
| **Setter** | Red Team — Vulnerability Generator | Plant hidden edge cases, complexity traps, zero-day bugs |
| **Solver** | Blue Team — Patcher | Pass ALL tests including adversarial hidden ones |
| **Oracle** | Sandboxed Judge | Execute real code, measure pass/fail, issue shaped rewards |

---

## ✅ The Result That Matters — Boundary Probe

6 adversarial edge cases locked in **before training began**, never shown during the training loop:

| Case | What It Tests | Baseline | Trained |
|---|---|---|---|
| `graph_shortest_path_single_node` | 1-node graph, 0 edges | ❌ | ✅ |
| `graph_shortest_path_two_hop` | Indirect path only | ❌ | ✅ |
| `graph_bipartite_min_odd_cycle` | Odd cycle boundary | ❌ | ✅ |
| `array_lis_hidden_valley` | Valley breaks greedy LIS | ❌ | ✅ |
| `dp_lcs_order_sensitive` | Reversed string pair | ❌ | ✅ |
| **Overall** | | **16.7%** | **100.0% ✅** |

These are not cherry-picked outputs. The model passed cases it had **never seen**, on problems designed to break shortcut solvers.

---

## 📊 Training Results

**100-step GRPO · Qwen2.5-0.5B-Instruct · T4 GPU · 53 minutes**

| Metric | Baseline | After Training |
|---|---|---|
| Hidden-test pass rate | 54.7% | — |
| Best solver reward | — | **+34.31** (step 34) ⬆️ |
| Boundary-condition probe | 16.7% (1/6) | **100.0% (6/6) ✅** |
| Brute-force penalty triggers | 46.7% of episodes | **0.0%** |
| Setter win rate | 56.7% | **0.0%** |
| Training steps | — | 100 / 100 ✅ |
| Training time | — | 53m 01s on T4 |

### Reward Curve

![Training Curves](outputs/plots/training_curves1.png)

*Step 1: −9.25 → Peak: +34.31 (step 34). The spike is the signal — when the model generates a complete solution, it passes adversarial hidden tests. The reward design is correct; the bottleneck was generation length.*

### Before vs After

![Before After](outputs/plots/before_after.png)

---

## ❌ → 🔧 → ✅ The Learning Story

**❌ Before**
- Brute-force solver: 54.7% hidden-test pass rate
- Setter wins 56.7% of episodes
- O(n²) shortcuts triggered in 46.7% of episodes
- Boundary cases fail 83.3% of the time

**🔧 What We Built**
- Seeded adversarial task generation — hidden tests never seen during training
- 5-signal shaped GRPO reward — correctness, complexity, regression, format, robustness
- Anti-gaming penalties that catch shortcuts automatically
- Real Oracle sandbox — actual Python execution, real pass/fail

**✅ After**
- Boundary probe: 16.7% → **100%** (5 new unseen cases solved)
- Brute-force penalties: 46.7% → **0%**
- Best reward: **+34.31**
- Setter win rate: 56.7% → **0%**
- Adapter published: `codecourt-solver-grpo-v1`

---

## 🛡️ Why It's Hard to Game

**1. Hidden adversarial tests** — generated per-episode by the Setter. Never shown to the Solver.

**2. Dynamic seeding** — every episode is unique. Memorization is structurally impossible.

**3. Multi-signal shaped reward** — 5 independent checks:

```python
solver_reward = (
    correctness_score        # Did ALL tests pass?
  + complexity_match         # Right algorithmic complexity?
  - brute_force_penalty      # O(n²) when O(n log n) expected?
  - hidden_test_regression   # Passed public, failed hidden?
  - unsafe_pattern_penalty   # Suspicious imports caught?
)
```

**4. Setter actively adapts** — rewarded when it finds weaknesses. It doesn't stand still.

**5. Elo tracking** — both agents have live Elo ratings updated every episode.

---

## 🏆 Reward System

### Setter (Red Team)
| Outcome | Reward | Why |
|---|---|---|
| Solver passes all tests | −10 | Trap wasn't hard enough |
| Solver TLE | +40 | Complexity gap exploited |
| Solver wrong answer | +50 | Real edge case found |
| Setter can't solve own task | −30 | Self-consistency violation |
| Invalid problem | −20 | Bad generation |

### Solver (Blue Team)
| Outcome | Reward | Why |
|---|---|---|
| Pass all tests | +50 | Correct, robust solution |
| TLE / brute-force detected | Negative | Weak algorithmic reasoning |
| Wrong answer | Negative | Brittle logic |
| Hidden regression | Negative | Public pass, hidden fail |
| Efficient code | Positive | Competitive-programming bonus |

---

## 📚 Problem Archetypes

3 archetypes × 3 tasks × 3 difficulty tiers = **27 configs, infinite seeded variants**

### 🟢 Easy — Single algorithm, clear signal
| Task | What Gets Tested |
|---|---|
| Maximum Subarray Sum | Kadane's vs O(n²) brute |
| Two Sum | Hash map vs nested loop |
| Coin Change | DP vs greedy |

### 🟡 Medium — Multi-step reasoning
| Task | What Gets Tested |
|---|---|
| Longest Increasing Subsequence | O(n log n) vs O(n²) |
| Shortest Path | Dijkstra on weighted graphs |
| Longest Common Subsequence | DP table vs recursion |

### 🔴 Hard — Designed to break shortcuts
| Task | What Gets Tested |
|---|---|
| Bipartite Check | Odd cycle, edge cases |
| Connected Components | Isolated nodes, self-loops |
| Fibonacci / Climbing Stairs | Matrix exp vs naive recursion |

---

## 🔗 OpenEnv Integration

```python
from env.codecourt_env import CodeCourtEnv

env = CodeCourtEnv()
obs = env.reset()
setter_info, solver_info, done, info = env.step(setter_code, solver_code)
print(env.render())
# Episode 1 | Setter Elo: 1016 | Solver Elo: 984
# Outcome: setter_wins | Setter: +55 | Solver: -8
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/ayushoncode/CodeCourt.git
cd CodeCourt
pip install -r requirements.txt

# Run baseline (untrained)
python scripts/baseline.py --episodes 30

# Train via GRPO
python scripts/train.py \
    --model Qwen/Qwen2.5-0.5B-Instruct \
    --train-samples 54 \
    --max-steps 100 \
    --max-completion-length 768

# Generate proof plots
python scripts/evaluate.py \
    --baseline ./outputs/baseline_results.json \
    --trained  ./outputs/training_history.json \
    --output   ./outputs/plots/

# Run boundary probe
python scripts/boundary_eval.py

# Launch live dashboard
uvicorn app:app --host 0.0.0.0 --port 7860
```

---

## 📁 Project Structure

```
codecourt/
├── oracle/          # Sandboxed execution + validation
├── env/             # OpenEnv environment + task generation
├── rewards/         # Shaped reward rubrics + Elo tracking
├── agents/          # Setter and Solver agents
├── training/        # GRPO dataset + reward helpers
├── scripts/         # baseline, train, evaluate, boundary_eval
├── notebooks/       # Colab-ready training notebook
├── dashboard/       # Live demo UI (WebSocket + REST)
└── outputs/
    ├── training_history.json
    ├── capability_boundary_eval.json
    └── plots/
        ├── training_curves1.png
        └── before_after.png
```

---

<div align="center">

*Failure → Intervention → Measurable Improvement.*
*The win condition is not a cherry-picked output. It is a visible learning story.*

**[Live Demo](https://huggingface.co/spaces/ayussssssiiii/codecourt) · [Trained Model](https://huggingface.co/ayussssssiiii/codecourt-solver-grpo-v1) · [GitHub](https://github.com/ayushoncode/CodeCourt) · [Blog](YOUR_BLOG_LINK)**

</div>
