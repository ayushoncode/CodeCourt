"""
Deploy CodeCourt to a Hugging Face Space.

Usage:
    python scripts/deploy_space.py --space-id your-username/codecourt

Auth:
    Set HF_TOKEN in the environment or run `huggingface-cli login` first.
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPACE_APP_FILES = [
    "Dockerfile",
    "app.py",
    "README.md",
    "openenv.yaml",
    "requirements.txt",
    "dashboard",
    "env",
    "oracle",
    "rewards",
    "agents",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy CodeCourt to Hugging Face Spaces")
    parser.add_argument("--space-id", default=os.getenv("HF_SPACE_ID"))
    parser.add_argument("--token", default=os.getenv("HF_TOKEN"))
    parser.add_argument("--space-sdk", default="docker", choices=["static", "gradio", "streamlit", "docker"])
    parser.add_argument("--private", action="store_true")
    return parser.parse_args()


def copy_artifacts(staging_dir: Path) -> None:
    for rel_path in SPACE_APP_FILES:
        src = PROJECT_ROOT / rel_path
        dst = staging_dir / rel_path
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def main():
    load_dotenv()
    args = parse_args()
    if not args.space_id:
        raise SystemExit("Missing --space-id or HF_SPACE_ID")

    api = HfApi(token=args.token)
    api.create_repo(
        repo_id=args.space_id,
        repo_type="space",
        space_sdk=args.space_sdk,
        private=args.private,
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        staging_dir = Path(tmpdir) / "space"
        staging_dir.mkdir(parents=True, exist_ok=True)
        copy_artifacts(staging_dir)

        api.upload_folder(
            folder_path=str(staging_dir),
            repo_id=args.space_id,
            repo_type="space",
            commit_message="Deploy CodeCourt Space",
        )

    print(f"Deployed to https://huggingface.co/spaces/{args.space_id}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Space deploy failed: {exc}", file=sys.stderr)
        raise
