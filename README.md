# forgebot

> Make any git repository self-operating. Bots are files; the repository is the interface.

forgebot runs versioned Markdown bot definitions when repository events occur. Each bot receives bounded repository context, can use a local agent CLI, and returns a validated action plan. Runs are dry-run by default, so automation can be reviewed before it changes anything.

## What it does

```text
repository event
	-> matching bot manifest
	-> bounded git and repository context
	-> optional deterministic rules shim
	-> Claude Code, Codex, or aider
	-> typed, permission-checked actions
	-> dry-run preview or explicit apply
	-> JSONL run and action records
```

The project is deliberately local. forgebot does not provide an LLM or require a hosted API: it delegates to an agent CLI already installed and authenticated on your machine.

## Requirements

- Python 3.11 or newer
- Git
- One supported agent CLI: `claude`, `codex`, or `aider`

Install the package, including development tools:

```bash
python -m pip install -e '.[dev]'
```

## Technology stack

forgebot is a small Python application built around standard local command-line tools:

| Layer | Technology | Role |
| --- | --- | --- |
| Language | Python 3.11+ | Core runtime and bot orchestration. |
| CLI | Typer | Exposes `init`, `doctor`, `run`, `run-once`, `hook`, and inspection commands. |
| Terminal UI | Rich | Formats bot results, action previews, warnings, and diagnostic tables. |
| Manifest format | Markdown and YAML | Keeps bot instructions readable, reviewable, and versioned with the repository. |
| File events | watchdog | Watches a repository recursively for `file_added` and `file_changed` triggers. |
| Repository context | Git subprocesses and a Python repo map | Supplies recent commits, working-tree status, and a compact symbol outline. |
| Agent integration | Claude Code, Codex, or aider CLIs | Delegates reasoning to a tool the developer already uses locally. |
| GitHub integration | GitHub CLI (`gh`) | Applies comment and pull-request actions without handling tokens directly. |
| Optional screening | Pydantic AI and JEV | Filters low-value events before a full agent run when configured. |
| Packaging | setuptools and `pyproject.toml` | Installs the `forgebot` package and console script. |
| Quality tools | pytest, pytest-cov, and Ruff | Test coverage, test execution, and Python linting. |

The core runtime has no database, web server, queue, or hosted agent service. Local JSONL files provide lightweight run and action history, while Git remains the source of truth for bot definitions.

### Project layout

```text
forgebot/
	cli.py          Typer commands and terminal output
	engine.py       Trigger matching and bot execution
	manifest.py     Markdown/YAML manifest parsing
	context.py      Bounded Git and repository context
	repomap.py      Compact Python symbol map generation
	watcher.py      File events and Git hook integration
	backends.py     Claude, Codex, and aider adapters
	actions.py      Typed action plans and safe execution
	permissions.py  Permission scopes and enforcement
	github.py       GitHub CLI argument builders
	jev.py          Optional event-screening gate
```

## Quickstart

Run these commands from the root of a Git repository:

```bash
forgebot doctor
forgebot init
git config core.hooksPath .githooks
forgebot list-bots
forgebot context
forgebot run-once post-merge
```

`forgebot init` creates `.gitbot/bots/`, copies the documentation-refresh example, and writes `post-merge` and `pre-push` hook shims to `.githooks/`. The `git config` command enables those hooks for the repository.

To watch the repository continuously for file events:

```bash
forgebot run
```

To fire a single trigger explicitly:

```bash
forgebot run-once post-merge
forgebot run-once 'file_added(runs/7/metrics.json)'
```

All commands use dry-run behavior unless write execution is explicitly requested:

```bash
forgebot run-once post-merge --apply
```

Review bot manifests and the action preview before using `--apply`.

## Using forgebot in an application

forgebot is intended for repository workflows that have a clear event, a bounded input, and a small set of acceptable side effects. A typical application looks like this:

1. A Git hook or file watcher emits an event such as `post-merge` or `file_added(runs/**/metrics.json)`.
2. forgebot loads the matching Markdown manifests from `.gitbot/bots/`.
3. Each selected bot receives a bounded context containing the current commit, recent Git history, working-tree status, and a compact repository map.
4. An optional Python rules shim computes exact facts such as thresholds or metric deltas. Its output is added to the prompt as authoritative deterministic data.
5. The selected agent CLI returns a JSON action plan instead of directly editing files or calling GitHub.
6. forgebot validates every action against the bot's permissions and payload schema, previews it in dry-run mode, and records it in JSONL.
7. With `--apply`, supported local file, GitHub comment, or pull-request actions are executed.

This makes the tool useful for recurring repository operations such as:

- Refreshing documentation after a merge and opening a pull request only when documentation is stale.
- Reviewing newly created experiment metrics and writing a bounded triage note or GitHub comment.
- Turning repository events into pull requests with a predictable title, body, and scope.
- Running read-only maintenance checks on push or merge without granting the bot write access.

The bot is the application unit: its instructions, trigger, permissions, and optional rules shim travel together as files in Git. That makes behavior reviewable in code review and easy to disable by changing or removing a manifest.

### Example: a metrics triage bot

The repository includes [`examples/bots/runwatch.md`](examples/bots/runwatch.md), which reacts to a new metrics file:

```markdown
---
name: runwatch
description: Flags anomalies in new experiment runs.
permissions: [read:runs_dir, read:repo, write:files]
triggers:
	- file_added(runs/**/metrics.json)
rules_shim: .gitbot/bots/runwatch_rules.py
---
```

The rules shim produces exact comparisons against a rolling baseline. The agent is asked to quote those values and recommend follow-up work, while the manifest prevents unrelated writes. The same pattern works for other domains: put deterministic calculations in a script and reserve the agent for interpretation and structured next steps.

### Example: a documentation bot

After `forgebot init`, the generated `docrefresh` bot responds to `post-merge`. It can inspect the merge context and propose a pull request using `write:pr`, but it cannot modify arbitrary working-tree files unless `write:files` is also declared.

Use a read-only first pass while designing a bot:

```bash
forgebot list-bots
forgebot context
forgebot run-once post-merge --backend codex
```

Only after reviewing the printed actions should the same event be applied:

```bash
forgebot run-once post-merge --backend codex --apply
```

## Bot manifests

Bots are Markdown files in `.gitbot/bots/`. YAML frontmatter declares the bot contract; the Markdown body contains its instructions.

```markdown
---
name: docrefresh
description: Keeps documentation current after merges.
permissions: [read:repo, write:pr]
triggers: [post-merge]
---

## Instructions

Inspect the merge and open a pull request for stale documentation.
```

Supported manifest fields are:

| Field | Purpose |
| --- | --- |
| `name` | Required bot name. |
| `description` | Description shown by `forgebot list-bots`. |
| `permissions` | Explicit scopes the bot may use. |
| `triggers` | Events that activate the bot. `trigger` is also accepted. |
| `rules_shim` | Optional Python program whose output is authoritative deterministic context. |
| `screen` | Optional JEV event-screening prompt. |
| `screen_threshold` | Optional JEV threshold from `0` to `1`. |

The instruction body must be non-empty. Invalid YAML, unknown permissions, and invalid screening values stop the manifest from loading.

### Triggers

The current trigger forms are:

- `post-merge`
- `pre-push`
- `file_added(<glob>)`, for example `file_added(runs/**/metrics.json)`
- `file_changed(<glob>)`

Git hooks invoke `forgebot hook <name>`. The watcher emits file events while `forgebot run` is active.

### Permission scopes

Permissions are declared per bot and checked for every action:

- `read:repo` for repository files and Git metadata
- `read:runs_dir` for watched run files
- `write:files` for repository file changes
- `write:comments` for GitHub issue or pull-request comments
- `write:pr` for opening pull requests

## Action plans

Agent output must contain a JSON object with an `actions` array. The supported action kinds are:

- `no_op`
- `write_file` with `path` and `content`
- `comment` with a positive issue or pull-request `number` and non-empty `body`
- `create_pr` with a non-empty `title` and `body`

The engine validates the action kind, payload, required permission, and repository-safe path before execution. Writes inside `.git` and paths outside the repository are rejected.

## Backends

By default, forgebot chooses an available backend in this order: Claude Code, Codex, then aider. Select one explicitly with `--backend`:

```bash
forgebot run-once post-merge --backend codex
forgebot run-once post-merge --backend aider
```

For applied runs, aider is excluded unless selected explicitly. Claude Code and Codex are preferred because their backend commands provide stronger execution boundaries.

The backend receives the bot instructions, trigger, bounded context, action schema, and any rules-shim output. Claude Code is invoked with read and Git-only tools; Codex uses a read-only sandbox; aider runs with no automatic commits and dry-run behavior. forgebot still validates the returned action plan independently of the backend.

## CLI reference

| Command | Use |
| --- | --- |
| `forgebot init` | Create `.gitbot/`, install local hook shims, and copy the starter bot. |
| `forgebot doctor` | Check Git, agent CLIs, bot directory, and optional JEV configuration. |
| `forgebot list-bots` | List discovered bots, triggers, permissions, and descriptions. |
| `forgebot context` | Print the bounded context that would be supplied to a bot. |
| `forgebot run` | Watch the repository continuously for matching file events. |
| `forgebot run-once TRIGGER` | Fire one trigger; use `--apply` to execute actions. |
| `forgebot hook NAME` | Run a Git-hook trigger such as `post-merge` or `pre-push`. |

Most commands operate on the current working directory. Run them from the repository whose `.gitbot/` directory contains the bot definitions.

## State and audit records

forgebot stores local runtime data in `.gitbot/state/`:

- `runs.jsonl` records trigger results and bot outcomes.
- `actions.jsonl` records each planned, skipped, or applied action.

Do not put secrets in bot instructions or repository context. Review the generated state files and decide whether they belong in version control for your project.

## Optional JEV screening

Bots can use the optional JEV event gate with `screen` and `screen_threshold`. Install the extra and configure `TYPESAFE_API_KEY` before enabling it:

```bash
python -m pip install -e '.[jev]'
export TYPESAFE_API_KEY=...
```

Without a configured gate, ordinary bots continue to run; a gate failure is reported as a warning.

## Development

```bash
pytest
ruff check .
```

The `tests/` directory covers manifests, permissions, action validation, backends, triggers, context generation, and the execution engine. Examples are in `examples/bots/`.

## Safety and design

Read these before enabling write actions:

- [Architecture](docs/ARCHITECTURE.md)
- [Security model](docs/SECURITY_MODEL.md)
- [Roadmap](docs/ROADMAP.md)

The important defaults are read-only context, explicit permissions, typed actions, repository-bound paths, dry-run execution, and JSONL audit history.
