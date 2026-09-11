"""
Install Git Hooks
=================
Configures git to use the repository .githooks directory for pre-commit protection.
"""

import subprocess
import sys
from pathlib import Path


def install_hooks():
    repo_root = Path(__file__).resolve().parent.parent
    hooks_dir = repo_root / ".githooks"

    if not (repo_root / ".git").exists():
        print("ℹ Not a git repository yet. Initializing git config fallback...")
        try:
            subprocess.run(["git", "init"], cwd=repo_root, check=True)
        except Exception as err:
            print(f"Warning: git init failed: {err}")
            return

    try:
        subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo_root, check=True)
        print("✓ Successfully configured git hooks: core.hooksPath -> .githooks")
        print("  Pre-commit guardrail active: binary files and local vaults will be blocked.")
    except Exception as err:
        print(f"Error configuring hooks: {err}")
        sys.exit(1)


if __name__ == "__main__":
    install_hooks()
