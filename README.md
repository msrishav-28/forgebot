# forgebot

> Make any git repo self-operating. Bots are files. The repo is the interface.

Apps were software you opened and operated. **Bots are software you give a job to** — a name, its own instructions, its own permissions. forgebot is the runtime that makes that real inside a git repository, on the Claude Code / Codex subscription you already have.

No cloud. No billing. No app to open. `git clone → forgebot init → it works`.

## What a bot is

A bot is one markdown file in `.gitbot/bots/`:

```markdown
---
name: docrefresh
description: Regenerates stale README sections and inline comments after every merge.
permissions: [read:repo, write:pr]
triggers: [post-merge]
---

## Instructions
You are docrefresh. When a merge lands on main:
1. Read the diff since the last merge.
2. Find README sections and docstrings that the diff makes stale.
3. Regenerate them and open a PR titled `docs: auto-refresh after <sha>`.
Never invent numbers. Only quote what you read.
```

Versioned, diffable, forkable — the repo itself is the bot registry.

## Architecture (the kernel is ~150 lines)

| Module | File | Job |
|---|---|---|
| Manifest parser | `forgebot/manifest.py` | Read bot files: YAML frontmatter + instructions |
| Permissions | `forgebot/permissions.py` | Scope enforcement — read-only bots get no write tools |
| Agent backends | `forgebot/backends.py` | Shell out to `claude -p` / `codex exec` (user's own subscription) |
| Triggers | `forgebot/watcher.py` | File-watch + git hooks (`post-merge`, `pre-push`) |
| Engine | `forgebot/engine.py` | Trigger → context → rules shim → agent → permitted actions |
| CLI | `forgebot/cli.py` | `init`, `list-bots`, `run`, `run-once`, `hook` |
| Dashboard | `forgebot/tui.py` | Textual TUI: live view of bots firing (v0.1) |

## Quickstart

```bash
pip install -e .
cd your-repo
forgebot init            # scaffolds .gitbot/ with a template bot
git config core.hooksPath .githooks   # wire the post-merge trigger
forgebot list-bots
forgebot run             # watch + fire on triggers
git merge feature-x      # watch a bot do its job
```

Shipped bots live in `templates/` and `examples/` — including **runwatch**, the anomaly flagger for ML experiment runs.

## Principles

1. **Bots are files.** If it's not in git, it's not a bot.
2. **Permissions are enforced, not suggested.** A bot that declares `read:repo` literally cannot receive write tools.
3. **Deterministic rules, probabilistic prose.** A tiny `rules.py` shim does exact checks; the LLM only reads results and writes explanations. Never let the model invent numbers.
4. **BYO agent.** forgebot never bills you — it drives the Claude Code / Codex CLI you already pay for.

## Roadmap

- **v0** (this commit): local kernel, file + git-hook triggers, one flagship bot
- **v0.1**: Textual live dashboard
- **v1**: FastAPI webhook server (GitHub events), SQLite run history, `forgebot install <owner/bot>` library command
- **v2**: web gallery for the public bot library

Built by [@msrishav-28](https://github.com/msrishav-28). The docs bot is powered by [Tekshila](https://github.com/msrishav-28/Tekshila).
