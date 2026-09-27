# Changelog

## [0.2.0] - 2026-09-24

### Added

- `comment` and `create_pr` typed actions, executed through the official GitHub CLI
  with the same permission checks, dry-run previews, and audit logging as local
  writes. `gh` is invoked as argv lists only; forgebot never handles tokens.
- Optional Jev (TypeSafe AI) gatekeeper: bots may declare a `screen:` question and
  `screen_threshold:`; uninteresting events are skipped before any agent backend runs.
  Off unless `TYPESAFE_API_KEY` is set; install with `pip install 'forgebot[jev]'`.
  Fail-open: gate errors proceed with the run and log a warning.

### Changed

- The aider backend now runs with `--dry-run`, and is never auto-selected for
  `--apply` runs; choosing it explicitly prints a sandbox warning.
- `forgebot run` and `forgebot run-once` print per-bot results, including dry-run
  previews of the exact `gh` commands that would run.

### Fixed

- Test suite failures in `test_engine.py` (stale `safe_summary` assertion) and
  `test_manifest.py` (`mkdir` without `exist_ok`).

### Removed

- The TUI stub, the `textual` extra, and the v0.1 TUI promise. A real dashboard is
  planned for 0.3.0.
- Dead code: the duplicate `Bot.allows` permission check and unwired `forgebot tui`
  entry point.

### Known limitations

- GitHub webhook and GitHub App support are not implemented yet.
- The Jev gate requires the optional `jev` extra and a TypeSafe AI API key.
- `write:files` and both GitHub write scopes are enforced per action, but `--apply`
  remains a human decision; review previews before using it.

## [0.1.0] - 2026-09-22

### Added

- Local bot manifests with YAML frontmatter and Markdown instructions.
- File and git-hook triggers.
- Claude Code, Codex, and aider subprocess backends.
- Permission scopes and deterministic rules shims.
- Python repo-map context adapted from aider's repo-map concept.
- CLI commands for initialization, listing bots, watching, and one-shot runs.
- Initial documentation, attribution, and example bots.

### Known limitations

- GitHub webhook and GitHub App support are not implemented yet.
- External write actions are not yet represented by a typed action executor.
- The TUI is a planned v0.1 feature, not yet a complete dashboard.
- The current context and backend layers require further hardening before untrusted repositories are supported.
