"""Tests for .claude/skills/run-pipeline/scripts/gate.py."""

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "run-pipeline" / "scripts"))

from gate import decide, main  # noqa: E402

RUNNER = "session_runner"
TRIGGERS = [
    {"id": "trig_b", "name": "Pipeline: batch", "enabled": True,
     "persistent_session_id": RUNNER, "derived_state": {"prompt": "BATCH PROMPT"}},
    {"id": "trig_o", "name": "Pipeline: onboarding scan", "enabled": True,
     "persistent_session_id": RUNNER, "derived_state": {"prompt": "ONBOARDING PROMPT"}},
]


def usage(advice):
    return {"advice": advice}


def test_sends_stored_prompt_to_runner_at_proceed():
    out = decide("batch", TRIGGERS, usage("proceed"), "idle")
    assert out["action"] == "send"
    assert out["session_id"] == RUNNER
    assert out["message"].startswith("[Manual pipeline run]")
    assert out["message"].endswith("BATCH PROMPT")
    assert "trig_b" in out["fallback"]


def test_stops_when_task_missing():
    out = decide("onboarding", TRIGGERS[:1], usage("proceed"), None)
    assert out["action"] == "stop"
    assert "no enabled scheduled task" in out["reason"]


def test_stops_without_runner_session_or_prompt():
    no_runner = [dict(TRIGGERS[0], persistent_session_id=None)]
    assert "runner session" in decide("batch", no_runner, usage("proceed"), None)["reason"]
    no_prompt = [dict(TRIGGERS[0], derived_state={})]
    assert "stored prompt" in decide("batch", no_prompt, usage("proceed"), None)["reason"]


def test_stops_when_runner_busy():
    out = decide("batch", TRIGGERS, usage("proceed"), "working")
    assert out["action"] == "stop"
    assert "busy" in out["reason"]


def test_stops_when_runner_busy_enum_form():
    out = decide("batch", TRIGGERS, usage("proceed"), "SESSION_STATUS_BUCKET_WORKING")
    assert out["action"] == "stop"
    assert decide("batch", TRIGGERS, usage("proceed"),
                  "SESSION_STATUS_BUCKET_COMPLETED")["action"] == "send"


def test_pause_stops_even_with_force():
    out = decide("onboarding", TRIGGERS, usage("pause"), "idle", force=True)
    assert out["action"] == "stop"


def test_caution_needs_force_for_batch_only():
    assert decide("batch", TRIGGERS, usage("caution"), "idle")["action"] == "stop"
    forced = decide("batch", TRIGGERS, usage("caution"), "idle", force=True)
    assert forced["action"] == "send"
    assert forced["notes"]
    assert decide("onboarding", TRIGGERS, usage("caution"), "idle")["action"] == "send"


def test_missing_usage_sends_with_note():
    out = decide("batch", TRIGGERS, None, None)
    assert out["action"] == "send"
    assert out["notes"] == ["usage: not available"]


def test_cli_reads_stdin(capsys, monkeypatch):
    payload = {"triggers": TRIGGERS, "usage": usage("proceed"), "runner_bucket": "idle"}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert main(["--stage", "onboarding"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["trigger_id"] == "trig_o"
    assert out["message"].endswith("ONBOARDING PROMPT")
