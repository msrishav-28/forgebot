"""forgebot TUI — live dashboard of bots firing (v0.1, Textual).

Run: pip install 'forgebot[tui]' && forgebot tui
For now: tail .gitbot/state/runs.jsonl in panels. Panels per bot,
permission denials highlighted in red. Shipped next commit.
"""

from __future__ import annotations


def main() -> None:  # wired to `forgebot tui` in v0.1
    raise SystemExit("TUI lands in v0.1 — `forgebot run` tail-prints for now.")
