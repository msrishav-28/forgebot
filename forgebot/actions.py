"""Typed, permission-checked action plans and safe local execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from .github import comment_argv, pr_create_argv, run_gh
from .permissions import require

ALLOWED_KINDS = {"write_file", "no_op", "comment", "create_pr"}


def _audit_argv(argv: list[str]) -> list[str]:
    """Redact long text values before they reach the audit log."""
    redacted = list(argv)
    if "--body" in redacted:
        i = redacted.index("--body")
        redacted[i + 1] = f"<{len(redacted[i + 1])} chars>"
    return redacted


@dataclass(frozen=True)
class Action:
    kind: str
    payload: dict = field(default_factory=dict)
    required_scope: str = "read:repo"

    @property
    def key(self) -> str:
        raw = json.dumps({"kind": self.kind, "payload": self.payload}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class ActionPlan:
    actions: list[Action] = field(default_factory=list)

    @classmethod
    def from_json(cls, text: str) -> "ActionPlan":
        """Parse the first fenced or raw JSON object containing `actions`."""
        candidates = [text]
        if "```" in text:
            candidates.extend(part for part in text.split("```") if "actions" in part)
        for candidate in candidates:
            try:
                data = json.loads(candidate.strip().removeprefix("json").strip())
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and isinstance(data.get("actions"), list):
                actions = []
                for item in data["actions"]:
                    if not isinstance(item, dict) or item.get("kind") not in ALLOWED_KINDS:
                        raise ValueError("Action must be an object with a supported kind")
                    actions.append(Action(str(item["kind"]), dict(item.get("payload") or {}),
                                          str(item.get("required_scope", "read:repo"))))
                return cls(actions)
        raise ValueError("Backend output did not contain a valid JSON action plan")

    def validate(self, permissions: list[str], bot_name: str) -> None:
        for action in self.actions:
            if action.kind == "write_file":
                if not isinstance(action.payload.get("path"), str):
                    raise ValueError("write_file requires a string payload.path")
                if not isinstance(action.payload.get("content"), str):
                    raise ValueError("write_file requires a string payload.content")
                if action.required_scope != "write:files":
                    raise ValueError("write_file must require write:files")
            elif action.kind == "comment":
                number = action.payload.get("number")
                if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
                    raise ValueError("comment requires a positive integer payload.number")
                body = action.payload.get("body")
                if not isinstance(body, str) or not body.strip():
                    raise ValueError("comment requires a non-empty string payload.body")
                if action.required_scope != "write:comments":
                    raise ValueError("comment must require write:comments")
            elif action.kind == "create_pr":
                title = action.payload.get("title")
                if not isinstance(title, str) or not title.strip():
                    raise ValueError("create_pr requires a non-empty string payload.title")
                if not isinstance(action.payload.get("body"), str):
                    raise ValueError("create_pr requires a string payload.body")
                if action.required_scope != "write:pr":
                    raise ValueError("create_pr must require write:pr")
            require(permissions, action.required_scope, bot_name)

    def safe_summary(self) -> list[str]:
        return [f"{a.kind} [{a.key}]: {sorted(a.payload)}" for a in self.actions]


class ActionExecutor:
    def __init__(self, repo_root: Path, dry_run: bool = True):
        self.root = Path(repo_root).resolve()
        self.dry_run = dry_run
        self.audit_path = self.root / ".gitbot" / "state" / "actions.jsonl"
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"unsafe path outside repository: {relative}")
        if relative.startswith(".git/") or relative == ".git":
            raise ValueError("refusing to write inside .git")
        return candidate

    def execute(self, plan: ActionPlan, permissions: list[str], bot_name: str) -> list[dict]:
        plan.validate(permissions, bot_name)
        results = []
        for action in plan.actions:
            entry = {"action_key": action.key, "bot": bot_name, "kind": action.kind,
                     "dry_run": self.dry_run, "status": "planned"}
            audit = entry
            if action.kind == "write_file":
                path = self._safe_path(action.payload["path"])
                if not self.dry_run:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(action.payload["content"], encoding="utf-8")
                    entry["status"] = "applied"
                entry["path"] = str(path.relative_to(self.root))
            elif action.kind == "comment":
                argv = comment_argv(action.payload)
                entry["argv"] = argv
                if not self.dry_run:
                    proc = run_gh(argv, self.root)
                    entry["status"] = "applied"
                    entry["result"] = proc.stdout.strip()[:500]
                audit = dict(entry, argv=_audit_argv(argv))
            elif action.kind == "create_pr":
                argv = pr_create_argv(action.payload)
                entry["argv"] = argv
                if not self.dry_run:
                    proc = run_gh(argv, self.root)
                    entry["status"] = "applied"
                    entry["result"] = proc.stdout.strip()[:500]
                audit = dict(entry, argv=_audit_argv(argv))
            elif action.kind == "no_op":
                entry["status"] = "skipped"
            with self.audit_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(audit) + "\n")
            results.append(entry)
        return results
