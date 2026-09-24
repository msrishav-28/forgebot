"""forgebot CLI."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .context import build_context
from .engine import Engine
from .manifest import ManifestError, load_bots
from .watcher import install_git_hooks, run_hook, start_watching

app = typer.Typer(help="forgebot — make any git repo self-operating.")
console = Console()
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def _print_results(results: list[dict]) -> None:
    for r in results:
        if r.get("error"):
            console.print(f"[red]✗[/] {r['bot']}: {r['error']}")
            continue
        if r.get("gate") == "skip":
            console.print(f"[yellow]–[/] {r['bot']}: gate skipped (p={r.get('probability')})")
            continue
        console.print(
            f"[green]✓[/] {r['bot']} via {r.get('backend')}: "
            f"{len(r.get('actions', []))} action(s)"
        )
        if r.get("warning"):
            console.print(f"[yellow]warning[/]: {r['warning']}")
        for line in r.get("actions", []):
            console.print(f"    {line}")
        for entry in r.get("executed", []):
            if entry.get("argv"):
                console.print(f"    [{entry['status']}] {' '.join(entry['argv'])}")


@app.command()
def init():
    root = Path.cwd()
    bots_dir = root / ".gitbot" / "bots"
    bots_dir.mkdir(parents=True, exist_ok=True)
    tpl = TEMPLATES / "bots" / "docs-refresh.md"
    if tpl.exists() and not (bots_dir / tpl.name).exists():
        shutil.copy(tpl, bots_dir / tpl.name)
    for hook in install_git_hooks(root):
        console.print(f"[green]hook[/] {hook}")
    console.print("[green]✓[/] .gitbot/ ready — run `git config core.hooksPath .githooks`")


@app.command("list-bots")
def list_bots():
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
def context():
    """Print bounded git + repo-map context."""
    console.print(build_context(Path.cwd()))


@app.command()
def doctor():
    """Check local prerequisites and repository setup."""
    import shutil as _shutil
    checks = {"git": _shutil.which("git"), "claude": _shutil.which("claude"),
              "codex": _shutil.which("codex"), "aider": _shutil.which("aider"),
              ".gitbot/bots": (Path.cwd() / ".gitbot" / "bots").is_dir()}
    for name, value in checks.items():
        console.print(f"{'[green]✓[/]' if value else '[yellow]–[/]'} {name}: {value or 'not found'}")


@app.command()
def run(backend: str = typer.Option(None, help="claude | codex | aider")):
    console.print("[bold]forgebot[/] watching… (Ctrl-C to stop)")
    start_watching(Engine(Path.cwd(), backend, dry_run=True), Path.cwd(),
                   on_results=_print_results)


@app.command("run-once")
def run_once(trigger: str, backend: str = typer.Option(None), apply: bool = typer.Option(False, "--apply")):
    """Fire one trigger; defaults to safe dry-run mode."""
    results = Engine(Path.cwd(), backend, dry_run=not apply).on_trigger(trigger)
    _print_results(results)


@app.command()
def hook(name: str):
    run_hook(name, Path.cwd())


if __name__ == "__main__":
    app()
