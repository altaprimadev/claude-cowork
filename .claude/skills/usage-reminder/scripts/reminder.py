#!/usr/bin/env python3
"""Helpers for the usage-reminder skill.

Subcommands:
  tasks      List open pipeline items in every `active` registry repo, grouped
             by state. Prints JSON. Read-only (GitHub REST via `gh api`).
  next-fire  Read usage-status --json output on stdin and print when the next
             reminder should fire: five-hour resets_at + 1 minute, or now + 5h
             when the data is missing or stale. Prints JSON.
"""
import argparse
import calendar
import json
import subprocess
import sys
import time
from pathlib import Path

GRACE_SECONDS = 60
FALLBACK_SECONDS = 5 * 3600

# First matching group wins. Order: what needs the human first, then work in
# flight, then queues.
GROUPS = (
    ("needs_human", lambda labels, is_pr: "ai:needs-human" in labels),
    ("blocked", lambda labels, is_pr: "ai:blocked" in labels),
    ("changes_needed", lambda labels, is_pr: "ai:changes-needed" in labels),
    ("in_progress", lambda labels, is_pr: "ai:in-progress" in labels),
    ("review_passed", lambda labels, is_pr: is_pr and "ai:review-passed" in labels),
    ("ready", lambda labels, is_pr: "ai:ready" in labels),
    ("draft", lambda labels, is_pr: "ai:draft" in labels),
    ("new_brief", lambda labels, is_pr: "ai:brief" in labels and "ai:triaged" not in labels),
    ("open_pr", lambda labels, is_pr: is_pr),
)
# Labels that mark an item as finished or as output, not as a task.
IGNORED = {"ai:report"}


def active_repos(registry_path):
    import yaml
    data = yaml.safe_load(Path(registry_path).read_text()) or {}
    return [r["name"] for r in data.get("repos", []) if r.get("status") == "active"]


def classify(items):
    """Group GitHub issue-API items. Returns {group: [item summary]}."""
    groups = {name: [] for name, _ in GROUPS}
    for it in items:
        labels = {l["name"] if isinstance(l, dict) else l for l in it.get("labels", [])}
        if labels & IGNORED:
            continue
        is_pr = "pull_request" in it
        if not is_pr and not any(l.startswith("ai:") for l in labels):
            continue
        for name, match in GROUPS:
            if match(labels, is_pr):
                groups[name].append({"number": it["number"], "title": it["title"],
                                     "url": it.get("html_url", ""), "pr": is_pr,
                                     "updated_at": it.get("updated_at", "")})
                break
    return {k: v for k, v in groups.items() if v}


def fetch(repo):
    out = subprocess.run(
        ["gh", "api", f"repos/{repo}/issues?state=open&per_page=100"],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        lines = (out.stderr or out.stdout or "gh api failed").strip().splitlines()
        raise RuntimeError(lines[-1] if lines else "gh api failed")
    return json.loads(out.stdout)


def cmd_tasks(a):
    repos, errors = {}, {}
    for repo in active_repos(a.registry):
        try:
            groups = classify(fetch(repo))
        except Exception as e:  # report per repo, keep going
            errors[repo] = str(e)
            continue
        if groups:
            repos[repo] = groups
    total = sum(len(v) for g in repos.values() for v in g.values())
    print(json.dumps({"active_tasks": total, "repos": repos, "errors": errors}, indent=2))
    return 0


def next_fire(usage, now):
    """Return (epoch, source). source is 'reset' or 'fallback'."""
    try:
        iso = usage["windows"]["five_hour"]["resets_at_iso"]
        resets = calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ"))
        if resets > now:
            return resets + GRACE_SECONDS, "reset"
    except (KeyError, TypeError, ValueError):
        pass
    return now + FALLBACK_SECONDS, "fallback"


def cmd_next_fire(a):
    raw = sys.stdin.read().strip()
    try:
        usage = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        usage = None
    now = a.now if a.now is not None else int(time.time())
    at, source = next_fire(usage, now)
    print(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(at)),
                      "source": source}))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tasks", help="list open pipeline items per active repo")
    t.add_argument("--registry", required=True, help="path to registry/repos.yml")
    n = sub.add_parser("next-fire", help="next reminder time from usage-status --json on stdin")
    n.add_argument("--now", type=int, help="override current epoch (for tests)")
    a = p.parse_args(argv)
    return cmd_tasks(a) if a.cmd == "tasks" else cmd_next_fire(a)


if __name__ == "__main__":
    sys.exit(main())
