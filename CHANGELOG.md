# Changelog

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
