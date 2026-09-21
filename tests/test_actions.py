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
