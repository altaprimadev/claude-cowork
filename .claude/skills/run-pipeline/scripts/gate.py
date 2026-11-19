#!/usr/bin/env python3
"""Decide whether the run-pipeline skill may fire a pipeline scheduled task now.

Reads one JSON object on stdin:
  triggers       the `data` list from list_triggers (enabled: true)
  usage          usage-status --json output, or null when not available
  runner_bucket  get_session status_bucket of the trigger's runner session, or null

Usage:
  gate.py --stage batch|onboarding [--force]
Prints {"action": "fire" | "stop", "trigger_id", "trigger_name", "reason", "notes"}.
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


def decide(stage, triggers, usage, runner_bucket, force=False):
    name = TRIGGER_NAMES[stage]
    out = {"action": "stop", "trigger_id": None, "trigger_name": name, "reason": "", "notes": []}
    match = [t for t in (triggers or []) if t.get("name") == name]
    if not match:
        out["reason"] = f"no enabled scheduled task named '{name}'"
        return out
    trig = match[0]
    out["trigger_id"] = trig.get("id")
    if not trig.get("enabled", True):
        out["reason"] = f"'{name}' is disabled"
        return out
    if runner_bucket == "working":
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
        out["notes"].append("usage advice is caution; fired with force")
    out["action"] = "fire"
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stage", choices=sorted(TRIGGER_NAMES), default="batch")
    p.add_argument("--force", action="store_true", help="fire a batch run at caution")
    a = p.parse_args(argv)
    raw = sys.stdin.read().strip()
    data = json.loads(raw) if raw else {}
    print(json.dumps(decide(a.stage, data.get("triggers"), data.get("usage"),
                            data.get("runner_bucket"), a.force), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
