"""Trigger-to-agent execution kernel."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .actions import ActionPlan
from .backends import BackendError, pick_backend
from .context import build_context
from .manifest import Bot, load_bots
from .permissions import PermissionDenied
from .watcher import matches

STATE_DIR = ".gitbot/state"


class Engine:
    def __init__(self, repo_root: Path, backend_name: str | None = None):
        self.repo_root = Path(repo_root)
        self.backend_name = backend_name
        (self.repo_root / STATE_DIR).mkdir(parents=True, exist_ok=True)

    def _git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=self.repo_root, capture_output=True, text=True)
        return result.stdout.strip()

    def run_rules_shim(self, bot: Bot, trigger: str) -> str:
        if not bot.rules_shim:
            return ""
        proc = subprocess.run([sys.executable, bot.rules_shim, trigger], cwd=self.repo_root,
                              capture_output=True, text=True)
        return proc.stdout.strip()

    def on_trigger(self, trigger: str) -> list[dict]:
        results = []
        for bot in load_bots(self.repo_root):
            if not any(t == trigger or matches(t, trigger) for t in bot.triggers):
                continue
            try:
                results.append(self.run_bot(bot, trigger))
            except (PermissionDenied, BackendError) as exc:
                results.append({"bot": bot.name, "error": str(exc)})
        self._record(trigger, results)
        return results

    def run_bot(self, bot: Bot, trigger: str) -> dict:
        context = build_context(self.repo_root)
        shim = self.run_rules_shim(bot, trigger)
        prompt = f"{bot.instructions}\n\n=== TRIGGER ===\n{trigger}\n\n=== CONTEXT ===\n{context}"
        if shim:
            prompt += f"\n\n=== DETERMINISTIC RULES (exact; do not contradict) ===\n{shim}"
        result = pick_backend(self.backend_name).run(prompt, cwd=str(self.repo_root))
        # v0 accepts textual agent output for display/logging; external writes
        # become typed ActionPlan operations in the next executor milestone.
        plan = ActionPlan()
        plan.validate(bot.permissions, bot.name)
        return {"bot": bot.name, "trigger": trigger, "backend": result.backend,
                "exit_code": result.exit_code, "output": result.output[:4000],
                "actions": plan.safe_summary()}

    def _record(self, trigger: str, results: list[dict]) -> None:
        with (self.repo_root / STATE_DIR / "runs.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"trigger": trigger, "results": results}) + "\n")
