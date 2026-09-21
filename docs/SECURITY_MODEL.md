# Security model

forgebot executes software-adjacent automation, so convenience must not outrun trust boundaries.

## Action execution flow

```text
agent output
   ↓
extract structured JSON
   ↓
validate action kind and payload schema
   ↓
validate manifest permission scope
   ↓
validate repository-safe path
   ↓
dry-run preview (default)
   ↓
explicit --apply for local writes
   ↓
audit JSONL record
```

The default is dry-run. Textual model output never directly performs a write. Only supported typed actions can reach the executor.

## Threats

- Prompt injection in README files, issues, source code, or generated artifacts.
- A malicious bot manifest requesting broad write permissions.
- Agent CLI escape through shell commands or inherited credentials.
- A bot leaking environment variables into comments or pull requests.
- Spoofed GitHub webhooks or replayed events.
- A dependency or GitHub Action compromise.

## Required controls

- Review manifests before enabling them.
- Default new bots to read-only and require explicit approval for writes.
- Keep credentials out of prompts and repository context.
- Bound context size and exclude `.env`, keys, tokens, and ignored secrets.
- Use dry-run mode before write mode.
- Make action execution typed, logged, idempotent, and permission-checked.
- Validate GitHub webhook signatures and reject replays.
- Keep GitHub Actions permissions minimal and dependencies updated.

## Safe rollout

1. Local read-only mode.
2. Local write mode with user approval.
3. Pull-request-only writes.
4. GitHub App with repository-scoped permissions.
5. Fully automated writes only for narrowly bounded actions.
