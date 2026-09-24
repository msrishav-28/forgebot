from pathlib import Path

import pytest

from forgebot.actions import Action, ActionExecutor, ActionPlan
from forgebot.permissions import PermissionDenied


def test_parse_action_plan():
    plan = ActionPlan.from_json('{"actions":[{"kind":"no_op","payload":{},"required_scope":"read:repo"}]}')
    assert plan.actions[0].kind == "no_op"


def test_write_requires_permission(tmp_path: Path):
    plan = ActionPlan([Action("write_file", {"path": "out.txt", "content": "x"}, "write:files")])
    with pytest.raises(PermissionDenied):
        ActionExecutor(tmp_path).execute(plan, ["read:repo"], "bot")


def test_path_traversal_rejected(tmp_path: Path):
    plan = ActionPlan([Action("write_file", {"path": "../outside.txt", "content": "x"}, "write:files")])
    with pytest.raises(ValueError, match="outside"):
        ActionExecutor(tmp_path).execute(plan, ["write:files"], "bot")


def test_dry_run_does_not_write(tmp_path: Path):
    plan = ActionPlan([Action("write_file", {"path": "out.txt", "content": "x"}, "write:files")])
    result = ActionExecutor(tmp_path, dry_run=True).execute(plan, ["write:files"], "bot")
    assert result[0]["status"] == "planned"
    assert not (tmp_path / "out.txt").exists()


def test_apply_writes(tmp_path: Path):
    plan = ActionPlan([Action("write_file", {"path": "out.txt", "content": "x"}, "write:files")])
    ActionExecutor(tmp_path, dry_run=False).execute(plan, ["write:files"], "bot")
    assert (tmp_path / "out.txt").read_text() == "x"


def test_comment_requires_write_comments_scope():
    plan = ActionPlan([Action("comment", {"number": 1, "body": "x"}, "write:pr")])
    with pytest.raises(ValueError, match="write:comments"):
        plan.validate(["write:pr", "write:comments"], "bot")


def test_comment_rejects_bad_number():
    plan = ActionPlan([Action("comment", {"number": "7", "body": "x"}, "write:comments")])
    with pytest.raises(ValueError, match="positive integer"):
        plan.validate(["write:comments"], "bot")


def test_comment_dry_run_previews_argv(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):
        pytest.fail("gh must not run in dry-run mode")

    monkeypatch.setattr("forgebot.actions.run_gh", _boom)
    plan = ActionPlan([Action("comment", {"number": 3, "body": "hi"}, "write:comments")])
    result = ActionExecutor(tmp_path, dry_run=True).execute(plan, ["write:comments"], "bot")
    assert result[0]["status"] == "planned"
    assert result[0]["argv"][:2] == ["issue", "comment"]


def test_comment_apply_runs_gh(tmp_path, monkeypatch):
    calls = []

    class _Proc:
        stdout = "https://github.com/octo/repo/issues/3#issuecomment-1\n"
        returncode = 0

    def fake_run_gh(argv, cwd, timeout=120.0):
        calls.append(argv)
        return _Proc()

    monkeypatch.setattr("forgebot.actions.run_gh", fake_run_gh)
    plan = ActionPlan([Action("comment", {"number": 3, "body": "hi"}, "write:comments")])
    result = ActionExecutor(tmp_path, dry_run=False).execute(plan, ["write:comments"], "bot")
    assert result[0]["status"] == "applied"
    assert calls == [["issue", "comment", "3", "--body", "hi"]]


def test_audit_log_redacts_body(tmp_path, monkeypatch):
    class _Proc:
        stdout = "ok\n"
        returncode = 0

    monkeypatch.setattr(
        "forgebot.actions.run_gh", lambda argv, cwd, timeout=120.0: _Proc()
    )
    plan = ActionPlan([Action("comment", {"number": 3, "body": "secret text"}, "write:comments")])
    ActionExecutor(tmp_path, dry_run=False).execute(plan, ["write:comments"], "bot")
    audit = (tmp_path / ".gitbot" / "state" / "actions.jsonl").read_text(encoding="utf-8")
    assert "secret text" not in audit
    assert "<11 chars>" in audit


def test_create_pr_requires_write_pr_scope():
    plan = ActionPlan([Action("create_pr", {"title": "t", "body": "b"}, "write:comments")])
    with pytest.raises(ValueError, match="write:pr"):
        plan.validate(["write:pr", "write:comments"], "bot")


def test_create_pr_rejects_empty_title():
    plan = ActionPlan([Action("create_pr", {"title": " ", "body": "b"}, "write:pr")])
    with pytest.raises(ValueError, match="title"):
        plan.validate(["write:pr"], "bot")


def test_create_pr_dry_run_previews_argv(tmp_path):
    plan = ActionPlan([Action("create_pr", {"title": "t", "body": "b"}, "write:pr")])
    result = ActionExecutor(tmp_path, dry_run=True).execute(plan, ["write:pr"], "bot")
    assert result[0]["status"] == "planned"
    assert result[0]["argv"][:2] == ["pr", "create"]
