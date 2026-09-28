# Contributing to forgebot

Thanks for helping make git repositories self-operating.

## Development

```bash
git clone https://github.com/msrishav-28/forgebot.git
cd forgebot
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
pytest
```

Use Python 3.11 or newer. Keep changes small, typed where practical, and easy to review. Run `pytest -q` and `ruff check forgebot tests` before opening a pull request. Source lines stay at or below 100 characters. Never use `shell=True` in subprocess calls — build argv lists.

Tests run offline: they never call a model backend, and the `gh` CLI is not required to run the suite. The optional Jev gate has its own extra — `pip install -e '.[dev,jev]'` — needed only when working on `forgebot/jev.py`.

## Adding a bot

Bots belong in `.gitbot/bots/<name>.md` and must include YAML frontmatter with `name`, `description`, `permissions`, and `triggers`, followed by explicit instructions. Use the smallest permission set possible. Never place API keys, tokens, or personal data in a bot file.

## Reporting security issues

Do not open public issues for vulnerabilities. Follow the process in [SECURITY.md](SECURITY.md) so maintainers can respond before details are public.

## Pull requests

- Explain the user problem and proposed behavior.
- Add or update tests for behavior changes.
- Document new permissions, triggers, or security implications.
- Do not silently change existing bot behavior.
- Keep generated files and unrelated formatting out of the PR.
- Use short imperative commit prefixes: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `ci:`.

By contributing, you agree that your contributions are provided under the repository's MIT license.
