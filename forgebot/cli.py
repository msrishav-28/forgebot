"""forgebot CLI — init, list-bots, run, run-once, hook."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .engine import Engine
from .manifest import ManifestError, load_bots
from .watcher import install_git_hooks, run_hook, start_watching

app = typer.Typer(help="forgebot — make any git repo self-operating.")
console = Console()

Template = Path(__file__).resolve().parent.parent / "templates"


@app.command()
def init():
    """Scaffold .gitbot/ in the current repo and install git hooks."""
    root = Path.cwd()
    bots_dir = root / ".gitbot" / "bots"
    bots_dir.mkdir(parents=True, exist_ok=True)
    tpl = Template / "bots" / "docs-refresh.md"
    if tpl.exists() and not (bots_dir / tpl.name).exists():
        shutil.copy(tpl, bots_dir / tpl.name)
    for hook in install_git_hooks(root):
        console.print(f"[green]hook[/] {hook}")
    console.print("[green]✓[/] .gitbot/ ready — run `git config core.hooksPath .githooks`")


@app.command("list-bots")
def list_bots():
    """Show every bot declared in this repo."""
    try:
        bots = load_bots(Path.cwd())
    except ManifestError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(1)
    table = Table(title=".gitbot/bots/")
    for col in ("name", "triggers", "permissions", "description"):
        table.add_column(col)
    for b in bots:
        table.add_row(b.name, ", ".join(b.triggers), ", ".join(b.permissions), b.description)
    console.print(table)


@app.command()
def run(backend: str = typer.Option(None, help="claude | codex")):
    """Watch this repo and fire bots on triggers. Ctrl-C to stop."""
    console.print("[bold]forgebot[/] watching… (Ctrl-C to stop)")
    start_watching(Engine(Path.cwd(), backend), Path.cwd())


@app.command("run-once")
def run_once(trigger: str, backend: str = typer.Option(None)):
    """Fire a trigger manually — the demo command. e.g. `forgebot run-once post-merge`"""
    Engine(Path.cwd(), backend).on_trigger(trigger)


@app.command()
def hook(name: str):
    """Entry point for git hooks (.githooks/<hook> calls this)."""
    run_hook(name, Path.cwd())


if __name__ == "__main__":
    app()
