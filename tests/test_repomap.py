from pathlib import Path

from forgebot.repomap import build_repo_map


def test_repo_map_finds_symbols(tmp_path: Path):
    (tmp_path / "a.py").write_text("def important():\n    return 1\n")
    (tmp_path / "b.py").write_text("from a import important\nimportant()\n")
    result = build_repo_map(tmp_path)
    assert "important" in result
    assert "a.py" in result
