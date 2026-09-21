"""Trigger layer: file watching + git hooks.

v0 triggers:
  file_added(<glob>)   — watchdog events on a watched directory
  post-merge           — invoked from .githooks/post-merge via `forgebot hook post-merge`
  pre-push             — same pattern
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class BotFileHandler(FileSystemEventHandler):
    """Map filesystem events to file_added/file_changed triggers."""

    def __init__(self, engine, repo_root: Path):
        self.engine = engine
        self.repo_root = repo_root

    def on_created(self, event):
        if not event.is_directory:
            rel = str(Path(event.src_path).relative_to(self.repo_root))
            self.engine.on_trigger(f"file_added({rel})")

    def on_modified(self, event):
        if not event.is_directory:
            rel = str(Path(event.src_path).relative_to(self.repo_root))
            self.engine.on_trigger(f"file_changed({rel})")


def glob_of(trigger: str) -> str | None:
    """Extract the glob from a trigger like file_added(runs/**/metrics.json)."""
    if trigger.startswith(("file_added(", "file_changed(")) and trigger.endswith(")"):
        return trigger[trigger.index("(") + 1 : -1]
    return None


def matches(trigger: str, pattern: str) -> bool:
    """Does a concrete event trigger (file_added(runs/7/m.json)) match a bot's
    pattern trigger (file_added(runs/**/metrics.json))?"""
    kind, concrete = pattern[: pattern.index("(")], pattern[pattern.index("(") + 1 : -1]
    if not trigger.startswith(kind + "("):
        return False
    declared = glob_of(trigger)
    return declared is not None and (
        fnmatch.fnmatch(concrete, declared)
        or fnmatch.fnmatch(f"/{concrete}", f"*/{declared}")
    )


def run_hook(name: str, repo_root: Path) -> None:
    """Called by git hooks: `forgebot hook post-merge`."""
    from .engine import Engine

    Engine(repo_root).on_trigger(name)


def start_watching(engine, repo_root: Path) -> None:
    observer = Observer()
    observer.schedule(BotFileHandler(engine, repo_root), str(repo_root), recursive=True)
    observer.start()
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def install_git_hooks(repo_root: Path) -> list[Path]:
    """Write hook shims into .githooks/ (opt-in via core.hooksPath)."""
    hooks_dir = repo_root / ".githooks"
    hooks_dir.mkdir(exist_ok=True)
    written = []
    for hook in ("post-merge", "pre-push"):
        p = hooks_dir / hook
        p.write_text(f"#!/bin/sh\nforgebot hook {hook}\n", encoding="utf-8")
        p.chmod(0o755)
        written.append(p)
    return written


def current_head_sha(repo_root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown"
