# forgebot

> Make any git repo self-operating. Bots are files. The repo is the interface.

forgebot turns named Markdown bot definitions into triggered, permissioned developer automation. It runs with Claude Code, Codex, or aider and defaults to dry-run mode.

## Quickstart

```bash
pip install -e '.[dev]'
forgebot doctor
forgebot init
forgebot list-bots
forgebot context
forgebot run-once post-merge
```

All runs are dry-run by default. Use `--apply` only after reviewing the action preview:

```bash
forgebot run-once post-merge --apply
```

## Runtime

```text
git/file event → bot manifest → bounded context → deterministic rules
→ Claude/Codex/aider → typed JSON actions → permission/path validation
→ dry-run or explicit apply → JSONL audit log
```

## Why forgebot?

Unlike an interactive coding assistant, forgebot lets a repository declare what should happen after a trigger. Unlike a generic agent framework, it keeps bots portable, reviewable, and versioned in git.

## Safety

- Read-only by default.
- Explicit permission scopes.
- Structured actions instead of implicit model writes.
- Repository-bound path validation.
- JSONL audit history.
- No API key or hosted LLM dependency.

Read [ARCHITECTURE](docs/ARCHITECTURE.md), [ROADMAP](docs/ROADMAP.md), and [SECURITY_MODEL](docs/SECURITY_MODEL.md) before enabling write actions.
