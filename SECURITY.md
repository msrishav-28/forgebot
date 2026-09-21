# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| main | Yes |
| older releases | Best effort |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting feature if enabled, or contact the repository maintainer privately through the GitHub profile. Include reproduction steps, affected commit, impact, and a suggested mitigation if available.

We aim to acknowledge reports within 7 days and provide an initial assessment within 14 days.

## Bot safety

forgebot can launch developer CLIs and bots can eventually write files, comments, or pull requests. Treat bot manifests and agent output as untrusted until reviewed. Never grant `write:files`, `write:pr`, or `write:comments` unless the bot needs it. Never run a bot against an untrusted repository with host credentials available.

Report prompt-injection, permission-bypass, secret-leakage, command-injection, and unsafe GitHub workflow issues privately.
