from pathlib import Path

from forgebot.context import build_context


def test_context_contains_repo_map(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n")
    result = build_context(tmp_path)
    assert "REPO MAP" in result
    assert "hello" in result
