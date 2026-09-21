# Contributing to forgebot

Thanks for helping make git repositories self-operating.

## Development

```bash
git clone https://github.com/msrishav-28/forgebot.git
cd forgebot
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Use Python 3.11 or newer. Keep changes small, typed where practical, and easy to review. Run `pytest` before opening a pull request.

## Adding a bot

Bots belong in `.gitbot/bots/<name>.md` and must include YAML frontmatter with `name`, `description`, `permissions`, and `triggers`, followed by explicit instructions. Use the smallest permission set possible. Never place API keys, tokens, or personal data in a bot file.

## Pull requests

- Explain the user problem and proposed behavior.
- Add or update tests for behavior changes.
- Document new permissions, triggers, or security implications.
- Do not silently change existing bot behavior.
- Keep generated files and unrelated formatting out of the PR.

By contributing, you agree that your contributions are provided under the repository's MIT license.
