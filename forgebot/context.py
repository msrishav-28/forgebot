"""Build bounded, reproducible context for a bot run."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .repomap import build_repo_map


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "(git command unavailable)"


def build_context(root: Path, include_map: bool = True, max_chars: int = 12000) -> str:
    parts = [
        f"HEAD: {git_output(root, 'rev-parse', '--short', 'HEAD')}",
        "--- recent commits ---",
        git_output(root, 'log', '-5', '--oneline'),
        "--- working tree ---",
        git_output(root, 'status', '--short'),
    ]
    if include_map:
        parts.extend(["--- repo map ---", build_repo_map(root)])
    return "\n".join(parts)[:max_chars]
