# forgebot

> Make any git repo self-operating. Bots are files. The repo is the interface.

Apps were software you opened and operated. **Bots are software you give a job to** — a name, its own instructions, its own permissions. forgebot is the runtime that makes that real inside a git repository, on the Claude Code / Codex / aider CLI you already have.

No cloud. No billing. No LLM frameworks. No app to open. `git clone → forgebot init → it works`.

## Architecture

| Module | Job |
|---|---|
| Manifest parser | YAML frontmatter + Markdown instructions |
| Permissions | Enforced read/write scopes |
| Agent backends | Claude Code, Codex, or aider CLI |
| Repo map | Ranked symbol outline so bots understand the codebase |
| Triggers | File watching and git hooks |
| Engine | Trigger → context → rules → agent → permitted actions |
| CLI | `init`, `list-bots`, `run`, `run-once`, `hook` |

## Why no harness, LangChain, LangGraph, or LangSmith?

forgebot deliberately has zero LLM-framework dependencies.

- **No harness:** Claude Code, Codex, and aider already are agent harnesses. They own the model loop, tool execution, context handling, and safety controls. Adding another harness around them would duplicate the core runtime.
- **No LangChain:** LangChain is useful for composing prompts, tools, retrievers, and model providers. forgebot has a smaller primitive: trigger one named bot, pass context, run one backend. Direct subprocess calls are easier to inspect and debug.
- **No LangGraph:** LangGraph is designed for durable, stateful, multi-node agent workflows with branching, checkpoints, and human approval. forgebot's v0 workflow is deliberately linear. We should add a graph only when real bots need retries, approvals, fan-out, or long-running state.
- **No LangSmith:** LangSmith is valuable for hosted tracing, evaluation, and observability. forgebot is local-first and BYO-subscription. v0 records local JSONL runs; a future OpenTelemetry exporter can provide portable traces without forcing a hosted SaaS dependency.

This is not anti-framework. It is scope discipline: the kernel should remain understandable in one sitting.

## Quickstart

```bash
pip install -e .
cd your-repo
forgebot init
git config core.hooksPath .githooks
forgebot list-bots
forgebot run
```

## Principles

1. Bots are files.
2. Permissions are enforced, not suggested.
3. Deterministic rules handle numbers; models write explanations.
4. BYO agent: Claude Code, Codex, or aider.
5. Start with direct primitives; introduce frameworks when complexity proves they are needed.

## Roadmap

- v0: local kernel, file/git triggers, flagship bots, agent adapters
- v0.1: Textual live dashboard and repo-map context injection
- v1: GitHub webhooks, SQLite run history, installable bot library, portable tracing
- v2: web gallery and multi-step bot graphs when justified

## Acknowledgements

The repo-map implementation is adapted from the repo-map concept in [aider](https://github.com/Aider-AI/aider), Apache-2.0. See [NOTICE](NOTICE).

Built by [@msrishav-28](https://github.com/msrishav-28).