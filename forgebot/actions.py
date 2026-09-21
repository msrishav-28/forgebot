"""Typed action boundary for future external writes.

The engine should produce an ActionPlan rather than letting model text
implicitly perform side effects. This v0 boundary validates declared scopes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .permissions import require


@dataclass(frozen=True)
class Action:
    kind: str
    payload: dict = field(default_factory=dict)
    required_scope: str = "read:repo"


@dataclass
class ActionPlan:
    actions: list[Action] = field(default_factory=list)

    def validate(self, permissions: list[str], bot_name: str) -> None:
        for action in self.actions:
            require(permissions, action.required_scope, bot_name)

    def safe_summary(self) -> list[str]:
        return [f"{a.kind}: {sorted(a.payload)}" for a in self.actions]
