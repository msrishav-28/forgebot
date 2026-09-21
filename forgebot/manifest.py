"""Parse and validate .gitbot/bots/*.md manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .permissions import validate

FRONTMATTER_DELIM = "---"


class ManifestError(ValueError):
    pass


@dataclass
class Bot:
    name: str
    path: Path
    description: str = ""
    permissions: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    rules_shim: str | None = None
    instructions: str = ""

    def allows(self, scope: str) -> bool:
        return scope in self.permissions


def parse_manifest(path: Path) -> Bot:
    text = path.read_text(encoding="utf-8")
    parts = text.split(FRONTMATTER_DELIM, 2)
    if len(parts) < 3:
        raise ManifestError(f"{path}: missing YAML frontmatter delimiters")
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise ManifestError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(meta, dict) or "name" not in meta:
        raise ManifestError(f"{path}: frontmatter must contain 'name'")
    instructions = parts[2].strip()
    if not instructions:
        raise ManifestError(f"{path}: empty instruction body")
    trigger = meta.get("trigger") or meta.get("triggers") or []
    if isinstance(trigger, str):
        trigger = [trigger]
    permissions = [str(p) for p in (meta.get("permissions") or [])]
    try:
        validate(permissions)
    except PermissionError as exc:
        raise ManifestError(f"{path}: {exc}") from exc
    shim = meta.get("rules_shim")
    if shim is None and (path.parent / "rules.py").exists():
        shim = str(path.parent / "rules.py")
    return Bot(str(meta["name"]), path, str(meta.get("description", "")), permissions,
               [str(t) for t in trigger], str(shim) if shim else None, instructions)


def load_bots(repo_root: Path) -> list[Bot]:
    bots_dir = repo_root / ".gitbot" / "bots"
    if not bots_dir.is_dir():
        return []
    return [parse_manifest(p) for p in sorted(bots_dir.glob("*.md"))]
