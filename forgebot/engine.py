"""The forgebot engine — the kernel.

trigger fired →
  match bots declaring that trigger →
    check permissions → build context (git log/diff) →
      run rules shim (deterministic checks, if any) →
        call agent backend with instructions + context →
          apply only the actions the bot is permitted to take.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .backends import BackendError, pick_backend
from .manifest import Bot, load_bots
from .permissions import PermissionDenied, require
from .watcher import current_head_sha, matches

STATE_DIR = ".gitbot/state"


class Engine:
    def __init__(self, repo_root: Path, backend_name: str | None = None):
        self.repo_root = Path(repo_root)
        self.backend_name = backend_name
        (self.repo_root / STATE_DIR).mkdir(parents=True, exist_ok=True)

    # --- context builders (all require read:repo) -----------------------

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.repo_root, capture_output=True, text=True
        ).stdout.strip()

    def build_context(self, bot: Bot) -> str:
        require(bot.permissions, "read:repo", bot.name)
        return (
            f"HEAD: {current_head_sha(self.repo_root)}\n"
            f"--- git log -5 --oneline ---\n{self._git('log', '-5', '--oneline')}\n"
            f"--- last merge diffstat ---\n"
            f"{self._git('diff', '--stat', 'HEAD@{1}', 'HEAD')}\n"
        )

    def run_rules_shim(self, bot: Bot, trigger: str) -> str:
        """Deterministic checks live OUTSIDE the model. Returns shim stdout."""
        if not bot.rules_shim:
            return ""
        proc = subprocess.run(
            [sys.executable, bot.rules_shim, trigger],
            cwd=self.repo_root, capture_output=True, text=True,
        )
        return proc.stdout.strip()

    # --- core -----------------------------------------------------------

    def on_trigger(self, trigger: str) -> list[dict]:
        results = []
        for bot in load_bots(self.repo_root):
            hit = any(
                t == trigger or matches(t, trigger) for t in bot.triggers
            )
            if not hit:
                continue
            print(f"🤖 [{bot.name}] fired by `{trigger}`")
            try:
                results.append(self.run_bot(bot, trigger))
            except (PermissionDenied, BackendError) as exc:
                print(f"⛔ [{bot.name}] {exc}")
                results.append({"bot": bot.name, "error": str(exc)})
        self._record(trigger, results)
        return results

    def run_bot(self, bot: Bot, trigger: str) -> dict:
        context = self.build_context(bot)
        shim_out = self.run_rules_shim(bot, trigger)
        prompt = (
            f"{bot.instructions}\n\n"
            f"=== TRIGGER ===\n{trigger}\n\n"
            f"=== REPO CONTEXT ===\n{context}\n"
        )
        if shim_out:
            prompt += f"\n=== RULES SHIM (exact results — never contradict) ===\n{shim_out}\n"

        backend = pick_backend(self.backend_name)
        result = backend.run(prompt, cwd=str(self.repo_root))
        entry = {
            "bot": bot.name,
            "trigger": trigger,
            "backend": result.backend,
            "exit_code": result.exit_code,
            "output": result.output[:4000],
        }
        print(result.output)
        return entry

    def _record(self, trigger: str, results: list[dict]) -> None:
        log = self.repo_root / STATE_DIR / "runs.jsonl"
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"trigger": trigger, "results": results}) + "\n")
