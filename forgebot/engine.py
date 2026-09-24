"""Trigger-to-agent execution kernel with typed action plans."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .actions import ActionExecutor, ActionPlan
from .backends import BackendError, pick_backend
from .context import build_context
from .github import GitHubError
from .manifest import Bot, load_bots
from .permissions import PermissionDenied
from .watcher import matches

STATE_DIR = ".gitbot/state"

ACTION_SCHEMA = (
    "Available action kinds (use only what your manifest permissions allow):\n"
    "- no_op: payload {} with required_scope read:repo\n"
    "- write_file: payload {\"path\": str, \"content\": str}, requires write:files\n"
    "- comment: payload {\"number\": int, \"body\": str, \"repo\": optional str}, "
    "requires write:comments\n"
    "- create_pr: payload {\"title\": str, \"body\": str, \"head\": optional str, "
    "\"base\": optional str, \"repo\": optional str}, requires write:pr\n"
    "Return a JSON object only: {\"actions\":[{\"kind\":\"no_op\",\"payload\":{},"
    "\"required_scope\":\"read:repo\"}]}"
)


class Engine:
    def __init__(self, repo_root: Path, backend_name: str | None = None, dry_run: bool = True):
        self.repo_root = Path(repo_root)
        self.backend_name = backend_name
        self.dry_run = dry_run
        (self.repo_root / STATE_DIR).mkdir(parents=True, exist_ok=True)

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
            except (PermissionDenied, BackendError, GitHubError, ValueError) as exc:
                results.append({"bot": bot.name, "error": str(exc)})
        self._record(trigger, results)
        return results

    def run_bot(self, bot: Bot, trigger: str) -> dict:
        context = build_context(self.repo_root)
        shim = self.run_rules_shim(bot, trigger)
        prompt = (
            f"{bot.instructions}\n\n=== TRIGGER ===\n{trigger}\n\n=== CONTEXT ===\n{context}\n\n"
            f"{ACTION_SCHEMA}"
        )
        if shim:
            prompt += f"\n=== DETERMINISTIC RULES (exact; do not contradict) ===\n{shim}"
        result = pick_backend(self.backend_name).run(prompt, cwd=str(self.repo_root))
        try:
            plan = ActionPlan.from_json(result.output)
            executed = ActionExecutor(self.repo_root, dry_run=self.dry_run).execute(
                plan, bot.permissions, bot.name
            )
            error = None
        except ValueError as exc:
            plan = ActionPlan([])
            executed = []
            error = str(exc)
        return {"bot": bot.name, "trigger": trigger, "backend": result.backend,
                "exit_code": result.exit_code, "output": result.output[:4000],
                "actions": plan.safe_summary(), "executed": executed, "error": error}

    def _record(self, trigger: str, results: list[dict]) -> None:
        with (self.repo_root / STATE_DIR / "runs.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"trigger": trigger, "results": results}) + "\n")
