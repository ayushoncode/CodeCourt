---
base_model:
  - Qwen/Qwen2.5-0.5B-Instruct
library_name: peft
pipeline_tag: text-generation
tags:
  - peft
  - lora
  - trl
  - grpo
  - transformers
  - text-generation
  - code
  - code-reasoning
  - competitive-programming
  - adversarial-evaluation
language:
  - en
---

# CodeCourt Solver GRPO v1

`ayussssssiiii/codecourt-solver-grpo-v1` is a LoRA adapter for `Qwen/Qwen2.5-0.5B-Instruct` trained in the CodeCourt self-play environment. The goal is not generic chat quality; it is improving robustness on adversarial coding tasks where a separate "Setter" agent generates hidden tests and edge cases to break the "Solver".

The adapter is part of the broader CodeCourt project:

- GitHub: https://github.com/ayushoncode/CodeCourt
- Live demo: https://huggingface.co/spaces/ayussssssiiii/codecourt
- Colab notebook: https://colab.research.google.com/github/ayushoncode/CodeCourt/blob/main/notebooks/train_codecourt.ipynb

## Model Details

- Developed by: Ayush (`ayushoncode` / `ayussssssiiii`)
- Model type: PEFT LoRA adapter for causal language modeling
- Base model: `Qwen/Qwen2.5-0.5B-Instruct`
- Training method: TRL GRPO with sandbox-executed reward functions
- Primary use case: adversarial code solving in the CodeCourt environment
- Languages: English prompts and Python code generation

## What Makes This Model Different

CodeCourt turns adversarial pressure into the training signal:

1. A Setter agent creates programming problems plus hidden edge cases.
2. A Solver model generates code.
3. An Oracle executes that code against tests inside a sandbox.
4. GRPO rewards the Solver for passing hidden tests and penalizes shortcut behavior like brute force or clipped/invalid outputs.

This means the model is optimized for robustness under hidden evaluation, not just matching public examples.

## Training Data

The GRPO training dataset is generated procedurally from CodeCourt problem archetypes rather than scraped from a static benchmark. Each sample contains:

- a solver prompt built from a generated programming problem
- hidden/public test cases serialized as JSON
- the expected optimal complexity target
- archetype, task ID, difficulty, and variant seed metadata

The dataset generator cycles through multiple algorithmic archetypes and difficulties, including graph, array, and dynamic-programming style tasks.

## Training Procedure

The adapter was trained with the CodeCourt GRPO pipeline in [`scripts/train.py`](https://github.com/ayushoncode/CodeCourt/blob/main/scripts/train.py).

Core setup from the training script:

- Base model: `Qwen/Qwen2.5-0.5B-Instruct`
- LoRA rank: `r=16`
- LoRA alpha: `16`
- LoRA dropout: `0.0`
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`
- Max steps: `100`
- Train samples: `54`
- Learning rate: `5e-6`
- Per-device batch size: `1`
- Gradient accumulation steps: `4`
- GRPO generations per prompt: `4`
- Max prompt length: `768`
- Max completion length: `768`
- Sandbox time limit: `2.0s`
- Sandbox memory limit: `256 MB`

Rewarding is execution-based. The training loop uses:

- pass/fail behavior under real test execution
- complexity-aware reward shaping
- penalties for brute-force or risky patterns
- format rewards for parseable code outputs

## Training Results

From the committed training log in `outputs/training_history.json`:

- Logged GRPO reward points: `100`
- Best reward: `+34.31` at step `26`
- Final logged reward: `-13.125` at step `100`

The important takeaway is that training produced successful high-reward trajectories, but the run remained unstable. This is consistent with the project goal: proving end-to-end adversarial RL fine-tuning on coding tasks, not claiming final-state saturation.

Baseline comparison from `outputs/baseline_results.json`:

- Baseline solver mode: brute force
- Average hidden-test pass rate: `54.7%`
- Setter win rate: `56.7%`

Boundary probe from `outputs/capability_boundary_eval.json`:

- Baseline pass rate: `16.7%` (`1/6`)
- Trained/reference pass rate: `100%` (`6/6`)
- Improved cases: `5`

Improved boundary cases include:

- shortest path on a single-node graph
- shortest path requiring an indirect hop
- minimum odd cycle bipartite rejection
- LIS with a hidden valley pattern
- order-sensitive LCS behavior

## Intended Uses

This adapter is intended for:

- CodeCourt demos and research prototypes
- experiments in adversarial evaluation for code models
- studying execution-grounded reward shaping for code generation
- educational work on self-play or red-team/blue-team training loops

## Out-of-Scope Uses

This model is not intended as:

- a production coding copilot
- a secure code auditor
- a general-purpose programming benchmark leader
- a substitute for human review on safety-critical or security-critical code

## Risks and Limitations

- The published artifacts show meaningful improvement on the project's adversarial probes, but they do not establish broad superiority across standard coding benchmarks.
- The repository includes a committed smoke-run comparison package for the dashboard; not every dashboard number is a direct full-GRPO checkpoint metric.
- The model may still generate incomplete, inefficient, or unsafe code.
- Execution-grounded rewards can improve robustness on targeted tasks without guaranteeing generalization to unrelated domains.
- The adapter inherits limitations and biases from `Qwen/Qwen2.5-0.5B-Instruct`.

## How to Use

This repository is an adapter, so load it on top of the base instruct model.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model_id = "Qwen/Qwen2.5-0.5B-Instruct"
adapter_id = "ayussssssiiii/codecourt-solver-grpo-v1"

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
base_model = AutoModelForCausalLM.from_pretrained(base_model_id)
model = PeftModel.from_pretrained(base_model, adapter_id)

prompt = """You are solving a competitive-programming problem.
Return only Python code in a single fenced block.

Problem:
Given a graph, compute the shortest path from node 1 to node n.
"""

inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=512)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

For the full environment and demo pipeline, use the main project repo:

- https://github.com/ayushoncode/CodeCourt

## Evaluation Notes

The strongest evidence in the current artifact set is the adversarial boundary probe, where the trained/reference side solves all `6/6` locked edge cases while the baseline solves `1/6`.

That should be interpreted as:

- evidence of improvement on hidden adversarial edge cases
- evidence that the reward loop is doing something real
- not evidence of universal coding-model dominance

## Environmental Impact

The project README reports one representative GRPO run as:

- Hardware: NVIDIA T4 GPU
- Duration: `53m 01s`

The exact cloud provider and compute region were not recorded in the committed artifacts.

## Citation

If you use CodeCourt or this adapter, please cite the project repository:

```bibtex
@software{codecourt2026,
  title = {CodeCourt: Adversarial Code Auditing via Self-Play},
  author = {Ayush},
  year = {2026},
  url = {https://github.com/ayushoncode/CodeCourt}
}
```

## Contact

Project and model page owner: `ayussssssiiii`
