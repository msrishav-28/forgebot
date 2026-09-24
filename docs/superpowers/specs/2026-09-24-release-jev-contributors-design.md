# Design: forgebot 0.2.0 — Jev gatekeeper, release completion, contributor readiness

Date: 2026-09-24
Status: Locked (client approved "lock and build", spec review gate waived by client)
Repository: https://github.com/msrishav-28/forgebot

## Goals (three workstreams, one release)

1. Add "Jev" to forgebot as an optional event gatekeeper.
2. Make forgebot work end to end as intended and release-ready as 0.2.0 on PyPI.
3. Make the project welcoming to outside contributors; rewrite documentation last.

Sequencing: Option A (extend in place) ships as 0.2.0 first. Option B (plugin/extension
architecture, real dashboard) is 0.3.0 and starts after the 0.2.0 release. Push to GitHub
over HTTPS after every commit.

## 1. Jev gatekeeper

Jev is TypeSafe AI's "System One" decision-only model: it returns typed probability JSON
via an API and has a Python SDK (`TypeSafeClassifier`). It cannot replace LLM backends —
it is a cheap decision layer. Scope: gatekeeper only.

### Behavior

- A bot manifest may declare an optional `screen:` key: a screening question template
  (e.g. "Does this metrics.json diff contain an anomaly worth waking an assistant for?").
- When a trigger fires, before building context and waking the expensive AI backend,
  forgebot asks Jev the screening question about the event. Jev returns a typed
  probability; below threshold, the event is skipped with one audit line.
- Off by default: with no `TYPESAFE_API_KEY` configured, forgebot never calls Jev and
  behaves exactly as 0.1.0. The "no API key, no hosted dependency" promise stays true.
- Fail-open: if Jev errors, times out, or returns an unparseable response, forgebot
  proceeds with the run and logs a warning. The gate saves money; it is not a security
  wall.
- Shipped behind an optional extra: `pip install forgebot[jev]`. Core install has zero
  new dependencies. SDK package name and import path to be verified against official
  TypeSafe AI documentation at implementation time; the module must import lazily so a
  missing extra degrades to "gate off", never an ImportError.
- Threshold configurable per bot (`screen_threshold:`, default 0.5) and globally via
  env `FORGEBOT_JEV_THRESHOLD`.
- Audit: every gate decision (skip/pass/error-proceed) is recorded in
  `.gitbot/state/runs.jsonl`.

## 2. Release completion (0.2.0 scope)

### Test fixes (both currently failing on every OS, including CI)

- `tests/test_engine.py`: stale assertion expects pre-hash `safe_summary()` format
  (`"comment: ['body']"`); current API returns `"comment [40ce4f555df4c33f]: ['body']"`.
  Rewrite the test against the current API with real assertions.
- `tests/test_manifest.py`: test helper calls `mkdir(parents=True)` without
  `exist_ok=True`; fails on second invocation. Add `exist_ok=True`.

### Real write scopes via GitHub `gh` CLI

`write:comments` and `write:pr` move from declared-but-unimplemented to real:

- New typed action kinds: `comment` (issue/PR comment) and `create_pr` (title/body/head).
- Executed by invoking `gh` as an argv list — never a shell string — with no shell
  interpolation anywhere.
- Same permission checks as `write_file`; dry-run default prints the exact `gh` argv that
  would run; `--apply` executes; both paths append to `.gitbot/state/actions.jsonl`.
- If `gh` is missing or unauthenticated, `--apply` fails loudly with install/login
  instructions; dry-run still previews.
- `write:files` (working-tree writes) stays out of scope for 0.2.0 and remains declared
  but unimplemented; docs must say so plainly.

### Aider security gap

Aider runs unsandboxed. For 0.2.0: aider is excluded from automatic backend selection
when `--apply` is in effect; using it requires explicit `--backend aider` plus a printed
warning. Verify at build time whether aider has a read-only capability flag; if yes,
wire it, if no, document the limitation.

### Cleanup

- Remove the TUI stub (`forgebot/tui.py` raises SystemExit), the `textual` extra, and the
  ROADMAP TUI promise. Dashboard/TUI returns for real in 0.3.0 (Option B).
- Salvage `watcher.current_head_sha` into `context.py`, replacing the inline HEAD call.
- Delete `Bot.allows` (manifest.py:29): dead duplicate of the permissions.allowed check.
  Two sources of truth is worse than none. Client confirmation requested before deletion.
- Bump version to 0.2.0 (`pyproject.toml`, `forgebot/__init__.py`), CHANGELOG entry.

### Release mechanics

- PyPI trusted publishing (OIDC) via GitHub Actions — no stored tokens.
- Tag `v0.2.0` triggers test → build → publish → GitHub Release from CHANGELOG.
- CI matrix already covers Python 3.11–3.13.

## 3. Contributors and documentation

- Contributor infrastructure largely present (CI, scorecard, dependabot, issue/PR
  templates, CoC); keep and polish.
- Documentation rewrite happens LAST, after code is final: README (tech-stack badges
  allowed, no emojis), ARCHITECTURE.md, SECURITY_MODEL.md (gh token handling, Jev data
  flow), CONTRIBUTING.md, CHANGELOG 0.2.0.
- List any file deletions to the client before making them.

## Explicitly out of scope for 0.2.0

- Plugin/extension architecture, dashboard/TUI, `write:files` implementation: all 0.3.0
  (Option B).
- No force-push; if the remote diverges from local, report instead of overwriting.

## Git/push plan

- Local tree verified content-identical to `origin/main` (c00a62a); local `main` adopted
  remote history. Remote dependabot branches left untouched.
- Push over HTTPS using the system credential helper (GCM, browser login if prompted).
- This spec document is the first commit and the first push.
