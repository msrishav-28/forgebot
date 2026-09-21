"""Compact ranked Python symbol map for bot context.

Adapted from the repo-map concept in aider (Apache-2.0). This is a
stdlib-only implementation using ast and cross-file reference counts.
See NOTICE for attribution.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".gitbot"}


def _iter_py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if not SKIP_DIRS.intersection(p.relative_to(root).parts)]


def _symbols_for(path: Path) -> list[tuple[str, str, int]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, OSError):
        return []
    return [("def" if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class", n.name, n.lineno)
            for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def build_repo_map(repo_root: Path, max_lines: int = 80) -> str:
    root = Path(repo_root)
    files = _iter_py_files(root)
    if not files:
        return "(no Python files found)"
    tags = {f: _symbols_for(f) for f in files}
    texts = {f: f.read_text(encoding="utf-8", errors="ignore") for f in files}
    refs: Counter = Counter()
    for f, symbols in tags.items():
        for _, name, _ in symbols:
            pattern = re.compile(rf"\b{re.escape(name)}\b")
            refs[name] = sum(len(pattern.findall(t)) for other, t in texts.items() if other != f)
    ranked = sorted(files, key=lambda f: -sum(refs[n] for _, n, _ in tags[f]))
    lines = ["=== REPO MAP (ranked symbol outline) ==="]
    for path in ranked:
        symbols = sorted(tags[path], key=lambda x: -refs[x[1]])
        if not symbols:
            continue
        lines.append(f"{path.relative_to(root)}:")
        lines.extend(f"  {kind} {name} (line {line})" for kind, name, line in symbols[:8])
        if len(lines) >= max_lines:
            lines.append("  … (truncated)")
            break
    return "\n".join(lines)
