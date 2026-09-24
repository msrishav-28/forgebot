"""Scope-validation tests for action plans."""

import pytest

from forgebot.actions import Action, ActionPlan
from forgebot.permissions import PermissionDenied


def test_action_plan_validates_scopes():
    plan = ActionPlan([Action("no_op", {}, "read:repo")])
    plan.validate(["read:repo", "write:comments"], "bot")
    summary = plan.safe_summary()
    assert len(summary) == 1
    assert summary[0].startswith("no_op [")
    assert summary[0].endswith(": []")


def test_action_plan_denies_missing_scope():
    plan = ActionPlan([Action("no_op", {}, "write:comments")])
    with pytest.raises(PermissionDenied):
        plan.validate(["read:repo"], "bot")
