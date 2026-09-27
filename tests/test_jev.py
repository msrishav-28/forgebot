"""Jev gatekeeper tests — no network, no real SDK (faked via sys.modules)."""

import sys
import types

import pytest

from forgebot.jev import GateDecision, gate_configured, screen_event


@pytest.fixture
def fake_sdk(monkeypatch):
    """Install fake pydantic / pydantic_ai modules; returns a control dict."""
    control = {"probability": 0.9, "error": None}

    fake_pydantic = types.ModuleType("pydantic")

    class BaseModel:
        pass

    def Field(**kwargs):
        return None

    fake_pydantic.BaseModel = BaseModel
    fake_pydantic.Field = Field

    fake_ai = types.ModuleType("pydantic_ai")

    class Agent:
        def __init__(self, model, output_type=None):
            self.model = model

        def run_sync(self, prompt):
            if control["error"] is not None:
                raise control["error"]
            result = types.SimpleNamespace()
            result.output = types.SimpleNamespace(probability=control["probability"])
            return result

    fake_ai.Agent = Agent
    monkeypatch.setitem(sys.modules, "pydantic", fake_pydantic)
    monkeypatch.setitem(sys.modules, "pydantic_ai", fake_ai)
    return control


def test_gate_off_without_key(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    decision = screen_event("q", "event")
    assert decision.proceed and decision.reason == "gate-off"
    assert not gate_configured()


def test_key_without_extra_fails_open(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    monkeypatch.setitem(sys.modules, "pydantic_ai", None)
    decision = screen_event("q", "event")
    assert decision.proceed and decision.reason == "gate-off"
    assert "not installed" in decision.detail


def test_pass_above_threshold(monkeypatch, fake_sdk):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    fake_sdk["probability"] = 0.9
    decision = screen_event("Does this matter?", "file_added(x)")
    assert decision.proceed and decision.reason == "pass"
    assert decision.probability == 0.9


def test_skip_below_threshold(monkeypatch, fake_sdk):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    fake_sdk["probability"] = 0.1
    decision = screen_event("q", "e")
    assert not decision.proceed and decision.reason == "skip"


def test_custom_threshold(monkeypatch, fake_sdk):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    fake_sdk["probability"] = 0.9
    decision = screen_event("q", "e", threshold=0.95)
    assert not decision.proceed


def test_env_threshold(monkeypatch, fake_sdk):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    monkeypatch.setenv("FORGEBOT_JEV_THRESHOLD", "0.95")
    fake_sdk["probability"] = 0.9
    decision = screen_event("q", "e")
    assert not decision.proceed


def test_error_fails_open(monkeypatch, fake_sdk):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    fake_sdk["error"] = RuntimeError("boom")
    decision = screen_event("q", "event")
    assert decision.proceed and decision.reason == "error"
    assert "boom" in decision.detail


def test_engine_gate_skip_short_circuits(tmp_path, monkeypatch):
    from forgebot.engine import Engine

    manifest = tmp_path / ".gitbot" / "bots" / "gated.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "---\nname: gated\npermissions: [read:repo]\ntriggers: [post-merge]\n"
        "screen: Does this matter?\n---\n\nDo nothing.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "forgebot.engine.screen_event",
        lambda question, event, threshold=None: GateDecision(False, "skip", 0.1),
    )

    def _boom(prefer=None, applying=False):
        raise AssertionError("backend must not run when the gate skips")

    monkeypatch.setattr("forgebot.engine.pick_backend", _boom)
    result = Engine(tmp_path).on_trigger("post-merge")
    assert result[0]["gate"] == "skip"
    assert result[0]["backend"] == "jev-gate"
    assert result[0]["actions"] == []
