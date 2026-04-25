"""
CodeCourt solver training with TRL GRPO.

This script performs actual policy optimization instead of only simulating
episodes. It trains the solver policy against CodeCourt-generated problems,
using the sandboxed executor as the reward function.

Usage:
    python scripts/train.py --train-samples 54 --max-steps 30
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datasets import Dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import GRPOConfig, GRPOTrainer

from training.solver_grpo import make_solver_dataset, make_solver_reward_functions


def parse_args():
    parser = argparse.ArgumentParser(description="Train the CodeCourt solver with GRPO")
    parser.add_argument("--model", type=str, default=os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct"))
    parser.add_argument("--hf-token", type=str, default=os.getenv("HF_TOKEN"))
    parser.add_argument("--output-dir", type=str, default="./outputs/grpo_solver")
    parser.add_argument("--train-samples", type=int, default=54)
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--num-generations", type=int, default=4)
    parser.add_argument("--max-prompt-length", type=int, default=768)
    parser.add_argument("--max-completion-length", type=int, default=256)
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--save-steps", type=int, default=10)
    parser.add_argument("--time-limit", type=float, default=2.0)
    parser.add_argument("--memory-limit-mb", type=int, default=256)
    parser.add_argument("--use-unsloth", action="store_true", help="Load the base model through Unsloth")
    parser.add_argument("--baseline-path", type=str, default="./outputs/baseline_results.json")
    parser.add_argument("--plots-dir", type=str, default="./outputs/plots")
    parser.add_argument("--skip-plots", action="store_true")
    return parser.parse_args()


def load_policy(model_name: str, hf_token: str | None, use_unsloth: bool):
    if use_unsloth:
        from unsloth import FastLanguageModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=2048,
            load_in_4bit=True,
            dtype=None,
            token=hf_token,
        )
        model = FastLanguageModel.get_peft_model(
            model,
            r=16,
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            lora_alpha=16,
            lora_dropout=0.0,
            bias="none",
            use_gradient_checkpointing="unsloth",
        )
        return model, tokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        token=hf_token,
        device_map="auto",
    )
    return model, tokenizer


def save_training_manifest(args, dataset_rows: list[dict], output_dir: Path):
    manifest = {
        "model": args.model,
        "train_samples": len(dataset_rows),
        "max_steps": args.max_steps,
        "num_generations": args.num_generations,
        "time_limit": args.time_limit,
        "memory_limit_mb": args.memory_limit_mb,
    }
    with open(output_dir / "training_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def save_log_history(trainer: GRPOTrainer, output_dir: Path):
    with open(output_dir / "training_log_history.json", "w") as f:
        json.dump(trainer.state.log_history, f, indent=2)


def build_training_summary(log_history: list[dict]) -> dict:
    metric_rows = [row for row in log_history if isinstance(row, dict) and "step" in row]
    reward_rows = [row for row in metric_rows if "reward" in row or "reward_pass_rate" in row]
    if not reward_rows:
        return {
            "total_logged_steps": len(metric_rows),
            "reward_points_logged": 0,
            "final_step": None,
            "final_reward": None,
            "best_reward": None,
            "final_pass_rate": None,
            "best_pass_rate": None,
            "final_robustness": None,
            "best_robustness": None,
        }

    final = reward_rows[-1]
    reward_values = [row.get("reward") for row in reward_rows if row.get("reward") is not None]
    pass_values = [row.get("reward_pass_rate") for row in reward_rows if row.get("reward_pass_rate") is not None]
    robustness_values = [row.get("reward_robustness") for row in reward_rows if row.get("reward_robustness") is not None]
    return {
        "total_logged_steps": len(metric_rows),
        "reward_points_logged": len(reward_rows),
        "final_step": final.get("step"),
        "final_reward": final.get("reward"),
        "best_reward": max(reward_values) if reward_values else None,
        "final_pass_rate": final.get("reward_pass_rate"),
        "best_pass_rate": max(pass_values) if pass_values else None,
        "final_robustness": final.get("reward_robustness"),
        "best_robustness": max(robustness_values) if robustness_values else None,
    }


def save_training_summary(trainer: GRPOTrainer, output_dir: Path) -> dict:
    summary = build_training_summary(trainer.state.log_history)
    with open(output_dir / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def save_artifact_manifest(output_dir: Path, args, dataset_rows: list[dict], training_summary: dict):
    manifest = {
        "baseline_path": args.baseline_path,
        "training_log_path": str(output_dir / "training_log_history.json"),
        "training_manifest_path": str(output_dir / "training_manifest.json"),
        "training_summary_path": str(output_dir / "training_summary.json"),
        "final_model_path": str(output_dir / "final_model"),
        "plots_dir": args.plots_dir,
        "train_samples": len(dataset_rows),
        "max_steps": args.max_steps,
        "latest_metrics": training_summary,
    }
    with open(output_dir / "artifact_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def maybe_generate_plots(args, output_dir: Path):
    if args.skip_plots:
        return
    try:
        from scripts.evaluate import generate_reports
    except Exception as exc:
        print(f"Skipping plots: could not import evaluator ({exc})")
        return

    baseline_path = Path(args.baseline_path)
    trained_path = output_dir / "training_log_history.json"
    if baseline_path.exists():
        generate_reports(baseline_path, trained_path, Path(args.plots_dir))
    else:
        print(f"Skipping before/after plots: baseline not found at {baseline_path}")
        generate_reports(None, trained_path, Path(args.plots_dir))


def main():
    load_dotenv()
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_rows = make_solver_dataset(args.train_samples)
    dataset = Dataset.from_list(dataset_rows)
    reward_funcs = make_solver_reward_functions(
        time_limit=args.time_limit,
        memory_limit_mb=args.memory_limit_mb,
    )

    model, tokenizer = load_policy(args.model, args.hf_token, args.use_unsloth)
    peft_config = None if args.use_unsloth else LoraConfig(
        r=16,
        lora_alpha=16,
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    train_args = GRPOConfig(
        output_dir=str(output_dir),
        learning_rate=args.learning_rate,
        max_steps=args.max_steps,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_generations=args.num_generations,
        max_prompt_length=args.max_prompt_length,
        max_completion_length=args.max_completion_length,
        report_to=[],
        remove_unused_columns=False,
    )

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=reward_funcs,
        args=train_args,
        train_dataset=dataset,
        peft_config=peft_config,
    )

    trainer.train()
    trainer.save_model(str(output_dir / "final_model"))
    tokenizer.save_pretrained(str(output_dir / "final_model"))
    save_training_manifest(args, dataset_rows, output_dir)
    save_log_history(trainer, output_dir)
    training_summary = save_training_summary(trainer, output_dir)
    save_artifact_manifest(output_dir, args, dataset_rows, training_summary)
    maybe_generate_plots(args, output_dir)

    print(f"Saved trained solver artifacts to {output_dir / 'final_model'}")


if __name__ == "__main__":
    main()
