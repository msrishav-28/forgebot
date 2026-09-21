# Roadmap

The goal is not to make a large AI wrapper. The goal is to make bots portable, reviewable, and genuinely useful in real repositories.

## Phase 0 — trustworthy kernel

- Stable bot manifest schema.
- Trigger matching for git hooks and file events.
- Permission validation and typed action boundary.
- Bounded repo context and local run history.
- Unit tests, CI, security policy, and clear examples.

## Phase 1 — useful developer experience

- Textual live TUI.
- `forgebot install owner/repo/path` for bot packages.
- `forgebot validate` and `forgebot doctor`.
- More language-aware repo maps using tree-sitter behind an optional extra.
- Dry-run mode and approval mode for every write action.
- Structured JSON event logs.

## Phase 2 — GitHub-native operation

- GitHub App and webhook receiver.
- HMAC signature checks, replay protection, idempotency, and least-privilege installation permissions.
- Pull-request review bot, release-notes bot, stale-doc bot, and CI triage bot.
- SQLite or Postgres run history.

## Phase 3 — bot library and collaboration

- Public bot registry based on git repositories.
- Manifest validation in CI.
- Compatibility metadata for backends and permissions.
- Ratings, examples, install counts, and reproducible demos.
- Bot version pinning and lockfiles.

## Phase 4 — optional workflow graphs

Only after real usage demonstrates the need: retries, approval nodes, fan-out/fan-in, scheduled jobs, and durable state. At that point evaluate a graph runtime such as LangGraph against a small native state machine.

## North-star metrics

- Time from clone to first successful bot run.
- Percentage of runs that finish without manual repair.
- Permission-denial rate and unsafe-action prevention.
- Repeat usage per repository.
- Number of external contributors and accepted bot packages.
- Stars are a lagging signal; user success and retention come first.
