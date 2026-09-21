"""Parse .gitbot/bots/*.md manifests: YAML frontmatter + instruction body."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONTMATTER_DELIM = "---"


class ManifestError(ValueError):
    """Raised when a bot file is malformed."""


@dataclass
class Bot:
    """A forgebot bot: name, instructions, permissions, triggers."""

    name: str
    path: Path
    description: str = ""
    permissions: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    rules_shim: str | None = None  # path to rules.py next to the manifest
    instructions: str = ""

    def allows(self, scope: str) -> bool:
        from .permissions import allowed

        return allowed(self.permissions, scope)


def parse_manifest(path: Path) -> Bot:
    """Parse one bot file: ---\n<yaml>\n---\n<markdown instructions>."""
    text = path.read_text(encoding="utf-8")
    parts = text.split(FRONTMATTER_DELIM, 2)
    if len(parts) < 3:
        raise ManifestError(f"{path}: missing YAML frontmatter delimiters")
    meta = yaml.safe_load(parts[1]) or {}
    if not isinstance(meta, dict) or "name" not in meta:
        raise ManifestError(f"{path}: frontmatter must contain at least 'name'")
    instructions = parts[2].strip()
    if not instructions:
        raise ManifestError(f"{path}: empty instruction body")

    trigger = meta.get("trigger") or meta.get("triggers") or []
    if isinstance(trigger, str):
        trigger = [trigger]

    shim = meta.get("rules_shim")
    if shim is None and (path.parent / "rules.py").exists():
        shim = str(path.parent / "rules.py")

    return Bot(
        name=str(meta["name"]),
        path=path,
        description=str(meta.get("description", "")),
        permissions=[str(p) for p in (meta.get("permissions") or [])],
        triggers=[str(t) for t in trigger],
        rules_shim=str(shim) if shim else None,
        instructions=instructions,
    )


def load_bots(repo_root: Path) -> list[Bot]:
    """Load every bot in <repo>/.gitbot/bots/."""
    bots_dir = repo_root / ".gitbot" / "bots"
    if not bots_dir.is_dir():
        return []
    return [parse_manifest(p) for p in sorted(bots_dir.glob("*.md"))]
