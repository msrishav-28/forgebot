"""Backend selection and aider sandbox tests."""

import pytest

from forgebot import backends
from forgebot.backends import AgentResult, BackendError


def test_aider_argv_includes_dry_run(monkeypatch):
    captured = {}

    class _Proc:
        stdout = "{}"
        returncode = 0

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        return _Proc()

    monkeypatch.setattr(backends.subprocess, "run", fake_run)
    backends.AiderBackend().run("prompt", cwd=".")
    assert captured["argv"][0] == "aider"
    assert "--dry-run" in captured["argv"]


def test_pick_backend_excludes_aider_when_applying(monkeypatch):
    monkeypatch.setattr(backends.ClaudeBackend, "available", staticmethod(lambda: False))
    monkeypatch.setattr(backends.CodexBackend, "available", staticmethod(lambda: False))
    monkeypatch.setattr(backends.AiderBackend, "available", staticmethod(lambda: True))
    with pytest.raises(BackendError):
        backends.pick_backend(applying=True)
    assert isinstance(backends.pick_backend("aider", applying=True), backends.AiderBackend)


def _write_bot(tmp_path):
    manifest = tmp_path / ".gitbot" / "bots" / "b.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "---\nname: b\npermissions: [read:repo]\ntriggers: [post-merge]\n---\n\nDo nothing.\n",
        encoding="utf-8",
    )


class _FakeAider:
    name = "aider"

    def run(self, prompt, cwd, timeout=0):
        return AgentResult("aider", '{"actions":[]}', 0)


def test_aider_apply_emits_warning(tmp_path, monkeypatch):
    from forgebot.engine import Engine

    _write_bot(tmp_path)
    monkeypatch.setattr(
        "forgebot.engine.pick_backend", lambda prefer=None, applying=False: _FakeAider()
    )
    result = Engine(tmp_path, dry_run=False).on_trigger("post-merge")
    assert "aider" in (result[0]["warning"] or "")


def test_aider_dry_run_has_no_warning(tmp_path, monkeypatch):
    from forgebot.engine import Engine

    _write_bot(tmp_path)
    monkeypatch.setattr(
        "forgebot.engine.pick_backend", lambda prefer=None, applying=False: _FakeAider()
    )
    result = Engine(tmp_path, dry_run=True).on_trigger("post-merge")
    assert result[0]["warning"] is None
