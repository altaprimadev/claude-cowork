"""Tests for .claude/skills/run-pipeline/scripts/gate.py."""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "run-pipeline" / "scripts"))

from gate import decide, main  # noqa: E402

TRIGGERS = [
    {"id": "trig_b", "name": "Pipeline: batch", "enabled": True},
    {"id": "trig_o", "name": "Pipeline: onboarding scan", "enabled": True},
]


def usage(advice):
    return {"advice": advice}


def test_fires_batch_at_proceed():
    out = decide("batch", TRIGGERS, usage("proceed"), "idle")
    assert out["action"] == "fire"
    assert out["trigger_id"] == "trig_b"


def test_stops_when_task_missing():
    out = decide("onboarding", TRIGGERS[:1], usage("proceed"), None)
    assert out["action"] == "stop"
    assert "no enabled scheduled task" in out["reason"]


def test_stops_when_runner_busy():
    out = decide("batch", TRIGGERS, usage("proceed"), "working")
    assert out["action"] == "stop"
    assert "busy" in out["reason"]


def test_pause_stops_even_with_force():
    out = decide("onboarding", TRIGGERS, usage("pause"), "idle", force=True)
    assert out["action"] == "stop"


def test_caution_needs_force_for_batch_only():
    assert decide("batch", TRIGGERS, usage("caution"), "idle")["action"] == "stop"
    forced = decide("batch", TRIGGERS, usage("caution"), "idle", force=True)
    assert forced["action"] == "fire"
    assert forced["notes"]
    assert decide("onboarding", TRIGGERS, usage("caution"), "idle")["action"] == "fire"


def test_missing_usage_fires_with_note():
    out = decide("batch", TRIGGERS, None, None)
    assert out["action"] == "fire"
    assert out["notes"] == ["usage: not available"]


def test_cli_reads_stdin(capsys, monkeypatch):
    payload = {"triggers": TRIGGERS, "usage": usage("proceed"), "runner_bucket": "idle"}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert main(["--stage", "onboarding"]) == 0
    assert json.loads(capsys.readouterr().out)["trigger_id"] == "trig_o"
