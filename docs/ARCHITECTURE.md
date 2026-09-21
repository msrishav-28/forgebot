# Architecture

## Product model

forgebot turns a git repository into a small operating environment for named bots. A bot is a versioned Markdown manifest containing instructions, triggers, and permissions.

## Runtime flow

```text
filesystem or git event
        ↓
trigger matcher
        ↓
load and validate bot manifest
        ↓
bounded context builder (git metadata + repo map)
        ↓
deterministic rules shim
        ↓
Claude Code / Codex / aider adapter
        ↓
typed action boundary
        ↓
local JSONL run record
```

## Components

- `manifest.py`: parses human-readable bot definitions and validates permissions.
- `watcher.py`: converts file changes and git hooks into trigger events.
- `context.py`: creates bounded reproducible context; it must never silently upload a whole repository.
- `repomap.py`: extracts a compact Python symbol outline.
- `backends.py`: delegates model interaction to an installed agent CLI.
- `actions.py`: future-proof boundary between model output and external side effects.
- `engine.py`: coordinates the flow and records runs.

## Trust boundaries

1. **Repository → manifest:** a repository can contain malicious bot instructions. Treat manifests as code, review them before execution.
2. **Manifest → backend:** permissions and backend selection must be explicit. Do not pass write-capable tools to read-only bots.
3. **Model → action executor:** model prose must never directly execute an external write. Parse and validate typed actions first.
4. **GitHub → local runner:** future webhooks require signature validation, replay protection, least-privilege tokens, and idempotency keys.

## Design rule

Keep the kernel understandable without a framework. Add infrastructure only when it removes a demonstrated source of complexity.
