#!/usr/bin/env python3
"""Decide whether the run-pipeline skill may start a pipeline run now, and build the message.

A pipeline run must happen in the runner session, where the repos are attached.
fire_trigger starts a new session without repos, so the skill sends the
scheduled task's stored prompt to the runner session with send_message instead.

Reads one JSON object on stdin:
  triggers       the `data` list from list_triggers (enabled: true)
  usage          usage-status --json output, or null when not available
  runner_bucket  get_session status_bucket of the runner session, or null.
                 Short ('working') and enum ('SESSION_STATUS_BUCKET_WORKING') forms work.

Usage:
  gate.py --stage batch|onboarding [--force]
Prints {"action": "send" | "stop", "trigger_id", "trigger_name", "session_id",
        "message", "fallback", "reason", "notes"}.
Exit 0 either way; the action field carries the decision.
"""
import argparse
import json
import sys

TRIGGER_NAMES = {
    "batch": "Pipeline: batch",
    "onboarding": "Pipeline: onboarding scan",
}
# Same split as CLAUDE.md "Usage budget": the batch run can start heavy
# stages (design, planning, implementation); the onboarding scan is light.
HEAVY = {"batch"}
BUCKET_PREFIX = "SESSION_STATUS_BUCKET_"
HEADER = ("[Manual pipeline run] The human owner asked for this run from an interactive "
          "session with the run-pipeline skill. Below is the stored prompt of the scheduled "
          "task '{name}' ({id}), unchanged. Run it now as a normal scheduled run.")
FALLBACK = ("Run the stored prompt of the scheduled task '{name}' ({id}) now, as a normal "
            "scheduled run. Read it with list_triggers.")


def bucket(value):
    """Normalize a get_session status_bucket: 'SESSION_STATUS_BUCKET_WORKING' -> 'working'."""
    value = (value or "").strip()
    if value.upper().startswith(BUCKET_PREFIX):
        value = value[len(BUCKET_PREFIX):]
    return value.lower()


def stored_prompt(trig):
    return ((trig.get("derived_state") or {}).get("prompt") or trig.get("prompt") or "").strip()


def decide(stage, triggers, usage, runner_bucket, force=False):
    name = TRIGGER_NAMES[stage]
    out = {"action": "stop", "trigger_id": None, "trigger_name": name, "session_id": None,
           "message": "", "fallback": "", "reason": "", "notes": []}
    match = [t for t in (triggers or []) if t.get("name") == name]
    if not match:
        out["reason"] = f"no enabled scheduled task named '{name}'"
        return out
    trig = match[0]
    out["trigger_id"] = trig.get("id")
    out["session_id"] = trig.get("persistent_session_id")
    if not trig.get("enabled", True):
        out["reason"] = f"'{name}' is disabled"
        return out
    if not out["session_id"]:
        out["reason"] = f"'{name}' has no runner session (persistent_session_id)"
        return out
    prompt = stored_prompt(trig)
    if not prompt:
        out["reason"] = f"'{name}' has no stored prompt"
        return out
    if bucket(runner_bucket) == "working":
        out["reason"] = "the runner session is busy with another run"
        return out

    advice = (usage or {}).get("advice")
    if advice is None:
        out["notes"].append("usage: not available")
    elif advice == "pause":
        out["reason"] = "usage advice is pause"
        return out
    elif advice == "caution" and stage in HEAVY:
        if not force:
            out["reason"] = "usage advice is caution; the batch run may start a heavy stage"
            return out
        out["notes"].append("usage advice is caution; sent with force")

    fmt = {"name": name, "id": out["trigger_id"]}
    out["message"] = HEADER.format(**fmt) + "\n\n" + prompt
    out["fallback"] = FALLBACK.format(**fmt)
    out["action"] = "send"
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", choices=sorted(TRIGGER_NAMES), default="batch")
    p.add_argument("--force", action="store_true", help="send a batch run at caution")
    a = p.parse_args(argv)
    raw = sys.stdin.read().strip()
    data = json.loads(raw) if raw else {}
    print(json.dumps(decide(a.stage, data.get("triggers"), data.get("usage"),
                            data.get("runner_bucket"), a.force), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
