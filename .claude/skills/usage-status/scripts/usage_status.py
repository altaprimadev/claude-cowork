#!/usr/bin/env python3
"""Format plan usage-limit status from Claude Code rate-limit data.

Input (stdin or --file) can be any of:
  1. A list_events response (claude-code-remote MCP) filtered to rate_limit_event.
  2. A single rate_limit_info object.
  3. A Claude Code status line JSON with a `rate_limits` field.

Default output (reset time is for the five-hour window):
  remaining hour to reset: 1h30m
  usage percentage:
  - 5h: 29%
  - weekly: 70%

--json prints the overall advice, thresholds, capture time, and per-window
details. The overall advice follows the five-hour window only; the weekly
percent is informational. A window whose limit is reached (status neither
`allowed` nor `allowed_warning`) still pauses, because no request can run then. --policy reads thresholds from registry/policy.yml
(usage_budget.caution_pct, usage_budget.pause_pct).

Use --session-id to print the MCP session id for this cloud session.
"""
import argparse
import json
import os
import re
import sys
import time

WINDOWS = ("five_hour", "seven_day")
LABELS = {"five_hour": "5h", "seven_day": "weekly"}
DEFAULT_CAUTION = 70
DEFAULT_PAUSE = 90


def session_id():
    raw = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID", "")
    if not raw:
        sys.exit("error: CLAUDE_CODE_REMOTE_SESSION_ID is not set (not a cloud session)")
    _, _, suffix = raw.partition("_")
    return "session_" + (suffix or raw)


def load_thresholds(path):
    """Return (caution_pct, pause_pct) from policy.yml, or the defaults."""
    if not path:
        return DEFAULT_CAUTION, DEFAULT_PAUSE
    text = open(path).read()
    try:
        import yaml
        budget = (yaml.safe_load(text) or {}).get("usage_budget") or {}
    except ImportError:
        # Minimal fallback: read the two keys under `usage_budget:`.
        block = re.search(r"^usage_budget:\s*\n((?:[ \t]+.*\n?)*)", text, re.M)
        budget = {}
        if block:
            for k in ("caution_pct", "pause_pct"):
                m = re.search(rf"^\s+{k}:\s*(\d+)", block.group(1), re.M)
                if m:
                    budget[k] = int(m.group(1))
    caution = int(budget.get("caution_pct", DEFAULT_CAUTION))
    pause = int(budget.get("pause_pct", DEFAULT_PAUSE))
    if not 0 < caution < pause <= 100:
        sys.exit(f"error: invalid usage_budget in {path}: caution_pct={caution}, pause_pct={pause}")
    return caution, pause


def walk(node, created_at=None):
    """Yield (dict, nearest created_at) for every dict in a nested JSON structure."""
    if isinstance(node, dict):
        created_at = node.get("created_at", created_at)
        yield node, created_at
        for v in node.values():
            yield from walk(v, created_at)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v, created_at)


def extract(data):
    """Return (windows, status, captured_at) from the newest snapshot found.

    windows maps window name -> {"utilization": 0..1, "resets_at": epoch, "status": str}.
    """
    snapshots = []
    for d, created_at in walk(data):
        win = {}
        status = None
        # Shape 1/2: rate_limit_info with unifiedWindows.
        if isinstance(d.get("unifiedWindows"), dict):
            for name, w in d["unifiedWindows"].items():
                if isinstance(w, dict) and "utilization" in w and "resetsAt" in w:
                    win[name] = {"utilization": float(w["utilization"]),
                                 "resets_at": int(w["resetsAt"]),
                                 "status": w.get("status")}
            status = d.get("status")
        # Shape 3: status line rate_limits.
        elif isinstance(d.get("rate_limits"), dict):
            for name, w in d["rate_limits"].items():
                if isinstance(w, dict) and "used_percentage" in w and "resets_at" in w:
                    win[name] = {"utilization": float(w["used_percentage"]) / 100,
                                 "resets_at": int(w["resets_at"]),
                                 "status": None}
        if win:
            snapshots.append((win, status, created_at))
    if not snapshots:
        return None
    # list_events returns events oldest -> newest, so the last snapshot is newest.
    return snapshots[-1]


# Statuses that still allow requests. "allowed_warning" only means a warning
# threshold was crossed; the percent decides the advice.
ALLOWED_STATUSES = ("allowed", "allowed_warning")


def limit_reached(status):
    return bool(status) and status not in ALLOWED_STATUSES


def advice(pct, status, caution, pause):
    if limit_reached(status):
        return "pause"
    if pct >= pause:
        return "pause"
    if pct >= caution:
        return "caution"
    return "proceed"


def fmt_remaining(seconds):
    if seconds <= 0:
        return "0h0m (window already reset)"
    minutes = int(seconds // 60)
    days, rem = divmod(minutes, 1440)
    hours, mins = divmod(rem, 60)
    if days:
        return f"{days}d{hours}h{mins}m"
    return f"{hours}h{mins}m"


def build(data, now, caution, pause):
    """Return the full status dict, or raise ValueError with a message."""
    found = extract(data)
    if not found:
        raise ValueError("no rate-limit data found in input "
                         "(page further back in list_events, or the session has made no API call yet)")
    win, status, captured_at = found
    rows = {}
    for n in WINDOWS:
        if n not in win:
            continue
        w = win[n]
        left = w["resets_at"] - now
        reset = left <= 0
        pct = 0 if reset else round(w["utilization"] * 100)
        # A window that already reset is allowed again, whatever the old status said.
        st = "allowed" if reset else (w.get("status") or status)
        rows[n] = {"remaining_seconds": max(left, 0),
                   "remaining": fmt_remaining(left), "usage_percent": pct,
                   "resets_at_utc": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(w["resets_at"])),
                   "resets_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(w["resets_at"])),
                   "status": st, "advice": advice(pct, st, caution, pause)}
    if "five_hour" not in rows:
        raise ValueError(f"five_hour window not in data (found: {', '.join(win)})")
    overall = rows["five_hour"]["advice"]
    if any(limit_reached(r["status"]) for r in rows.values()):
        overall = "pause"
    return {"advice": overall, "captured_at": captured_at,
            "thresholds": {"caution_pct": caution, "pause_pct": pause},
            "windows": rows}


def render(result):
    rows = result["windows"]
    lines = [f"remaining hour to reset: {rows['five_hour']['remaining']}", "usage percentage:"]
    lines += [f"- {LABELS[n]}: {r['usage_percent']}%" for n, r in rows.items()]
    blocked = [LABELS[n] for n, r in rows.items() if limit_reached(r["status"])]
    if blocked:
        lines.append(f"status: limit reached ({', '.join(blocked)})")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", help="read JSON from this file instead of stdin")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--policy", help="registry/policy.yml with usage_budget thresholds")
    p.add_argument("--now", type=int, help="override current epoch (for tests)")
    p.add_argument("--session-id", action="store_true",
                   help="print the MCP session id for this cloud session and exit")
    a = p.parse_args(argv)

    if a.session_id:
        print(session_id())
        return 0

    caution, pause = load_thresholds(a.policy)
    raw = open(a.file).read() if a.file else sys.stdin.read()
    if not raw.strip():
        print("error: no input. Call list_events with kinds [\"rate_limit_event\"] first, "
              "then pass the last event on stdin (SKILL.md steps 1-3).", file=sys.stderr)
        return 1
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: input is not valid JSON: {e}", file=sys.stderr)
        return 1
    now = a.now if a.now is not None else int(time.time())
    try:
        result = build(data, now, caution, pause)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if a.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
