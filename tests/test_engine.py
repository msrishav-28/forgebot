from pathlib import Path

from forgebot.actions import Action, ActionPlan


def test_action_plan_validates_scopes():
    plan = ActionPlan([Action("comment", {"body": "ok"}, "write:comments")])
    plan.validate(["read:repo", "write:comments"], "bot")
    assert plan.safe_summary() == ["comment: ['body']"]
