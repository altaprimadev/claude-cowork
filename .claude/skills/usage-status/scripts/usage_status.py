#!/usr/bin/env python3
"""Format plan usage-limit status from Claude Code rate-limit data.

Input (stdin or --file) can be any of:
  1. A list_events response (claude-code-remote MCP) filtered to rate_limit_event.
  2. A single rate_limit_info object.
  3. A Claude Code status line JSON with a `rate_limits` field.

Default output (five-hour window):
  remaining hour to reset: 1h30m
  usage percentage: 29%

Use --session-id to print the MCP session id for this cloud session.
"""
import argparse
import json
import os
import sys
import time

WINDOWS = ("five_hour", "seven_day")


def session_id():
    raw = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID", "")
    if not raw:
        sys.exit("error: CLAUDE_CODE_REMOTE_SESSION_ID is not set (not a cloud session)")
    _, _, suffix = raw.partition("_")
    return "session_" + (suffix or raw)


def walk(node):
    """Yield every dict in a nested JSON structure."""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def extract(data):
    """Return (windows, captured_at, status) from the newest snapshot found.

    windows maps window name -> {"utilization": 0..1, "resets_at": epoch}.
    """
    snapshots = []
    order = 0
    for d in walk(data):
        # Shape 1/2: rate_limit_info with unifiedWindows.
        if "unifiedWindows" in d:
            win = {}
            for name, w in d["unifiedWindows"].items():
                if "utilization" in w and "resetsAt" in w:
                    win[name] = {"utilization": float(w["utilization"]),
                                 "resets_at": int(w["resetsAt"]),
                                 "status": w.get("status")}
            if win:
                snapshots.append((order, win, d.get("status")))
                order += 1
        # Shape 3: status line rate_limits.
        elif "rate_limits" in d and isinstance(d["rate_limits"], dict):
            win = {}
            for name, w in d["rate_limits"].items():
                if isinstance(w, dict) and "used_percentage" in w and "resets_at" in w:
                    win[name] = {"utilization": float(w["used_percentage"]) / 100,
                                 "resets_at": int(w["resets_at"]),
                                 "status": None}
            if win:
                snapshots.append((order, win, None))
                order += 1
    if not snapshots:
        return None
    # list_events returns events oldest -> newest, so the last snapshot is newest.
    # Within one window, higher utilization with the same reset is also newer.
    _, win, status = snapshots[-1]
    return win, status


def advice(pct, status):
    """Map usage to a work decision. Thresholds are documented in SKILL.md."""
    if status and status != "allowed":
        return "pause"
    if pct >= 90:
        return "pause"
    if pct >= 70:
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


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--file", help="read JSON from this file instead of stdin")
    p.add_argument("--window", default="five_hour", choices=WINDOWS)
    p.add_argument("--all", action="store_true", help="print every window found")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--now", type=int, help="override current epoch (for tests)")
    p.add_argument("--session-id", action="store_true",
                   help="print the MCP session id for this cloud session and exit")
    a = p.parse_args()

    if a.session_id:
        print(session_id())
        return

    raw = open(a.file).read() if a.file else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"error: input is not valid JSON: {e}")

    found = extract(data)
    if not found:
        sys.exit("error: no rate-limit data found in input "
                 "(page further back in list_events, or the session has made no API call yet)")
    win, status = found
    now = a.now if a.now is not None else int(time.time())

    names = [n for n in WINDOWS if n in win] if a.all else [a.window]
    if not a.all and a.window not in win:
        sys.exit(f"error: window '{a.window}' not in data (found: {', '.join(win)})")

    rows = []
    for n in names:
        w = win[n]
        left = w["resets_at"] - now
        pct = 0 if left <= 0 else round(w["utilization"] * 100)
        rows.append({"window": n, "remaining_seconds": max(left, 0),
                     "remaining": fmt_remaining(left), "usage_percent": pct,
                     "resets_at_utc": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(w["resets_at"])),
                     "resets_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(w["resets_at"])),
                     "status": w.get("status") or status,
                     "advice": advice(pct, w.get("status") or status)})

    if a.json:
        print(json.dumps(rows if a.all else rows[0], indent=2))
        return
    for i, r in enumerate(rows):
        if a.all:
            if i:
                print()
            print(f"[{r['window']}]")
        print(f"remaining hour to reset: {r['remaining']}")
        print(f"usage percentage: {r['usage_percent']}%")
        if r["status"] and r["status"] != "allowed":
            print(f"status: {r['status']} (limit reached)")


if __name__ == "__main__":
    main()
