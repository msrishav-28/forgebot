"""Agent backends: drive the user's existing Claude Code / Codex / aider CLI.

forgebot never bills for LLM calls. It shells out to whichever CLI the
user is already logged into, injecting the bot's instructions + context.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


class BackendError(RuntimeError):
    pass


@dataclass
class AgentResult:
    backend: str
    output: str
    exit_code: int


class ClaudeBackend:
    name = "claude"

    @staticmethod
    def available() -> bool:
        return shutil.which("claude") is not None

    def run(self, prompt: str, cwd: str, timeout: int = 600) -> AgentResult:
        proc = subprocess.run(
            ["claude", "-p", prompt, "--allowedTools", "Read,Grep,Glob,Bash(git:*)"],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return AgentResult(self.name, proc.stdout.strip(), proc.returncode)


class CodexBackend:
    name = "codex"

    @staticmethod
    def available() -> bool:
        return shutil.which("codex") is not None

    def run(self, prompt: str, cwd: str, timeout: int = 600) -> AgentResult:
        proc = subprocess.run(
            ["codex", "exec", "--sandbox", "read-only", prompt],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return AgentResult(self.name, proc.stdout.strip(), proc.returncode)


class AiderBackend:
    """Scriptable aider as an agent backend."""

    name = "aider"

    @staticmethod
    def available() -> bool:
        return shutil.which("aider") is not None

    def run(self, prompt: str, cwd: str, timeout: int = 900) -> AgentResult:
        proc = subprocess.run(
            ["aider", "--message", prompt, "--no-auto-commits", "--yes", "--dry-run"],
            cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return AgentResult(self.name, proc.stdout.strip(), proc.returncode)


def pick_backend(prefer: str | None = None, applying: bool = False):
    order = [ClaudeBackend, CodexBackend, AiderBackend]
    if prefer == "codex":
        order = [CodexBackend, ClaudeBackend, AiderBackend]
    elif prefer == "aider":
        order = [AiderBackend, ClaudeBackend, CodexBackend]
    if applying and prefer != "aider":
        order = [cls for cls in order if cls is not AiderBackend]
    for cls in order:
        if cls.available():
            return cls()
    raise BackendError("No agent CLI found. Log into `claude`, `codex`, or `aider` first.")
