# Security model

forgebot executes software-adjacent automation, so convenience must not outrun trust boundaries.

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
- Pin high-risk workflow actions to immutable commits before production use.

## Safe rollout

1. Local read-only mode.
2. Local write mode with user approval.
3. Pull-request-only writes.
4. GitHub App with repository-scoped permissions.
5. Fully automated writes only for narrowly bounded actions.

Never advertise autonomous writes as safe by default. The user should understand exactly what a bot can read and change.
