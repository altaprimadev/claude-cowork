#!/usr/bin/env python3
"""Build the pipeline status for the pipeline-status skill.

Read-only. The script fetches open issues and PRs with `gh api` (REST) for the
control repo and every `active` registry repo. The agent passes the session
data it reads through MCP tools on stdin:

  {"triggers": <list_triggers data>, "runner": <get_session result or null>,
   "usage": <usage-status --json or null>}

Output: Markdown for chat (default) or JSON (--json).

Usage:
  python3 status.py --registry <clone>/registry/repos.yml [--json] < input.json
"""
from __future__ import annotations

import argparse
import calendar
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CONTROL_REPO = "alta-prima-indonesia/claude-cowork"
PIPELINE_TASKS = ("Pipeline: batch", "Pipeline: onboarding scan")
WIB = 7 * 3600
STALE_SECONDS = 24 * 3600
DEP_LINE = re.compile(r"^Depends on:(.*)$", re.MULTILINE | re.IGNORECASE)
DEP_REF = re.compile(r"(?:([\w.-]+/[\w.-]+))?#(\d+)")
BUCKETS = {
    "SESSION_STATUS_BUCKET_WORKING": "working",
    "SESSION_STATUS_BUCKET_BLOCKED": "blocked",
    "SESSION_STATUS_BUCKET_REVIEW_READY": "idle",
    "SESSION_STATUS_BUCKET_COMPLETED": "idle",
    "SESSION_STATUS_BUCKET_FAILED": "failed",
}
# Fallback when the input has no status_bucket. Only values seen in get_session results.
SESSION_STATUS = {
    "SESSION_STATUS_IDLE": "idle",
    "SESSION_STATUS_PENDING": "working",
}


# ---------- input helpers ----------

def labels_of(item: dict) -> set[str]:
    return {l["name"] if isinstance(l, dict) else l for l in item.get("labels", [])}


def epoch(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        return calendar.timegm(time.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return None


def wib(ts: int | None) -> str:
    if ts is None:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M WIB", time.gmtime(ts + WIB))


def ref(repo: str, item: dict) -> dict:
    return {"repo": repo, "number": item["number"], "title": item.get("title", ""),
            "url": item.get("html_url", ""), "updated_at": item.get("updated_at", "")}


def unwrap(obj):
    """MCP results may wrap the payload in {"ccr": ...} or {"data": ...}."""
    while isinstance(obj, dict) and len(obj) == 1 and next(iter(obj)) in ("ccr", "data", "trigger"):
        obj = next(iter(obj.values()))
    return obj


# ---------- classification ----------

def runner_state(runner: dict | None) -> dict:
    runner = unwrap(runner) if runner else None
    if not isinstance(runner, dict) or not runner.get("id"):
        return {"state": "unknown"}
    meta = runner.get("external_metadata") or {}
    state = BUCKETS.get(runner.get("status_bucket", "")) or SESSION_STATUS.get(runner.get("session_status", ""), "unknown")
    return {"state": state,
            "id": runner["id"], "title": runner.get("title", ""),
            "task": runner.get("task_summary") or meta.get("task_summary") or "",
            "updated_at": runner.get("updated_at", "")}


def schedules(triggers) -> list[dict]:
    triggers = unwrap(triggers) or []
    out = []
    for t in triggers if isinstance(triggers, list) else []:
        if t.get("name") in PIPELINE_TASKS and t.get("enabled"):
            out.append({"name": t["name"], "next_run": epoch(t.get("next_run_at")),
                        "runner": t.get("persistent_session_id", "")})
    return sorted(out, key=lambda s: s["next_run"] or 0)


def open_deps(body: str, repo: str, open_numbers: dict[str, set[int]]) -> list[str]:
    """Dependencies still open. A dependency in a repo we could not read counts as open."""
    deps = []
    for line in DEP_LINE.findall(body or ""):
        for dep_repo, num in DEP_REF.findall(line):
            dep_repo = dep_repo or repo
            if dep_repo not in open_numbers or int(num) in open_numbers[dep_repo]:
                deps.append(f"{dep_repo}#{num}")
    return deps


def classify(data: dict[str, dict], now: int) -> dict[str, list[dict]]:
    """data: {repo: {"issues": [...issues API, PRs included...], "pulls": [...pulls API...]}}."""
    g = {k: [] for k in ("working", "agent_review", "merge", "human", "fix_queue",
                         "ready", "draft", "intake", "design", "waiting_deps", "stale")}
    open_numbers = {r: {i["number"] for i in d.get("issues", [])} for r, d in data.items()}
    for repo, d in data.items():
        pulls = {p["number"]: p for p in d.get("pulls", [])}
        pr_bodies = " ".join((p.get("body") or "") for p in pulls.values())
        for it in d.get("issues", []):
            labels = labels_of(it)
            if "ai:report" in labels:
                continue
            item = ref(repo, it)
            if "pull_request" in it:
                head = (pulls.get(it["number"]) or {}).get("head", {}).get("ref", "")
                item["head"] = head
                if "ai:needs-human" in labels or "ai:blocked" in labels:
                    g["human"].append(item)
                elif "ai:changes-needed" in labels:
                    g["fix_queue"].append(item)
                elif "ai:review-passed" in labels or head.startswith("design/"):
                    item["gate"] = "Gate 1 (design)" if head.startswith("design/") else "Gate 2 (code)"
                    g["merge"].append(item)
                elif head.startswith("ai/onboarding") or head.startswith("ai/registry-"):
                    item["gate"] = "onboarding"
                    g["merge"].append(item)
                elif head.startswith("ai/") and not it.get("draft"):
                    g["agent_review"].append(item)
                continue
            body = it.get("body") or ""
            is_task = "<!-- ai:plan" in body or "\nParent: " in "\n" + body
            if "ai:needs-human" in labels or "ai:blocked" in labels:
                item["label"] = "ai:needs-human" if "ai:needs-human" in labels else "ai:blocked"
                g["human"].append(item)
            elif "ai:in-progress" in labels:
                has_pr = re.search(rf"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#{it['number']}\b",
                                   pr_bodies, re.IGNORECASE)
                if has_pr:
                    continue  # its PR is listed instead
                updated = epoch(it.get("updated_at"))
                if updated is not None and now - updated > STALE_SECONDS:
                    item["idle_hours"] = (now - updated) // 3600
                    g["stale"].append(item)
                else:
                    g["working"].append(item)
            elif "ai:ready" in labels:
                g["ready"].append(item)
            elif "ai:draft" in labels:
                g["draft"].append(item)
            elif "ai:needs-design" in labels:
                g["design"].append(item)
            elif "ai:brief" in labels and "ai:triaged" not in labels:
                g["intake"].append(item)
            elif is_task and not any(l.startswith("ai:") for l in labels):
                item["deps"] = open_deps(body, repo, open_numbers)
                # Promote mode (batch B3) only moves planned tasks. Others need /answer to resume.
                item["planned"] = "<!-- ai:plan" in body
                g["waiting_deps"].append(item)
    for items in g.values():
        items.sort(key=lambda i: (i["repo"], i["number"]))
    return g


def short(i: dict) -> str:
    return f"{i['repo'].split('/')[-1]}#{i['number']}"


def next_heavy(groups: dict, usage: dict | None) -> str:
    advice = (usage or {}).get("advice")
    if advice in ("caution", "pause"):
        return f"nggak ada: usage advice {advice}, heavy item di-skip"
    busy = {i["repo"] for i in groups["working"] + groups["stale"]}
    if groups["fix_queue"]:
        i = groups["fix_queue"][0]
        return f"fix round {short(i)}"
    ready = [i for i in groups["ready"] if i["repo"] not in busy]
    if ready:
        i = ready[0]
        return f"implementasi {short(i)} (kandidat)"
    if groups["ready"]:
        return "nggak ada: repo yang punya task ready lagi ada task in-progress"
    if groups["design"]:
        i = groups["design"][0]
        return f"design {short(i)} (kandidat)"
    return "nggak ada: antrian heavy kosong"


def build(data, errors, triggers, runner, usage, now) -> dict:
    groups = classify(data, now)
    return {"now": now, "runner": runner_state(runner), "schedules": schedules(triggers),
            "usage": usage, "groups": groups, "next_heavy": next_heavy(groups, usage),
            "errors": errors}


# ---------- rendering (chat text, semi-casual Indonesian) ----------

def line(i: dict, extra: str = "") -> str:
    short = i["repo"].split("/")[-1]
    text = f"- [{short}#{i['number']}]({i['url']}) {i['title']}"
    return text + (f" ({extra})" if extra else "")


RUNNER_TEXT = {"working": "lagi jalan", "idle": "idle, nunggu jadwal atau merge",
               "blocked": "nunggu input", "failed": "run terakhir gagal", "unknown": "status nggak kebaca"}


def render(s: dict) -> str:
    g, out = s["groups"], []
    r = s["runner"]
    out.append("**Runner**")
    if r["state"] == "unknown":
        out.append("- status nggak kebaca")
    else:
        task = f": {r['task']}" if r.get("task") else ""
        out.append(f"- [{r['title'] or 'runner'}](https://claude.ai/code/{r['id']}) {RUNNER_TEXT[r['state']]}{task}")
    for sch in s["schedules"]:
        out.append(f"- {sch['name']}: berikutnya {wib(sch['next_run'])}")
    out.append("- Merge PR `ai/*` atau `design/*` langsung memicu run (pr-watch)")
    out.append(f"- Heavy item berikutnya: {s['next_heavy']}")

    sections = [
        ("Lagi dikerjain", [line(i) for i in g["working"]]
         + [line(i, "nunggu review agen") for i in g["agent_review"]]),
        ("Nunggu merge dari lu", [line(i, i.get("gate", "")) for i in g["merge"]]),
        ("Nunggu jawaban lu", [line(i, i.get("label", "")) for i in g["human"]]),
        ("Antrian run berikutnya", [line(i, "fix round") for i in g["fix_queue"]]
         + [line(i, "ready") for i in g["ready"]]
         + [line(i, "task review") for i in g["draft"]]
         + [line(i, "intake") for i in g["intake"]]
         + [line(i, "design") for i in g["design"]]),
        ("Nunggu dependency", [line(i, "nunggu " + ", ".join(d.split("/")[-1] for d in i["deps"]))
                               if i["deps"] else line(i, "dependency selesai, di-promote run berikutnya")
                               if i.get("planned", True)
                               else line(i, "tanpa label stage dan bukan task terencana; lanjutkan lewat /answer")
                               for i in g["waiting_deps"]]),
        ("Mandek", [line(i, f"ai:in-progress tanpa PR, {i['idle_hours']} jam nggak ada aktivitas")
                    for i in g["stale"]]),
    ]
    for title, lines in sections:
        if lines:
            out += ["", f"**{title}** ({len(lines)})"] + lines
    if s["errors"]:
        out += ["", "**Nggak kebaca**"] + [f"- {repo}: {err}" for repo, err in s["errors"].items()]
    u = s["usage"]
    if u and u.get("windows"):
        w = u["windows"]
        five = w.get("five_hour", {})
        week = w.get("seven_day", {})
        out += ["", f"usage: 5h {five.get('usage_percent', '?')}%, weekly {week.get('usage_percent', '?')}%, "
                    f"advice {u.get('advice', '?')}"]
    else:
        out += ["", "usage: not available"]
    return "\n".join(out)


# ---------- GitHub fetch ----------

def repos_to_read(registry_path: str) -> list[str]:
    import yaml
    data = yaml.safe_load(Path(registry_path).read_text()) or {}
    repos = [CONTROL_REPO]
    repos += [r["name"] for r in data.get("repos", []) if r.get("status") == "active" and r["name"] not in repos]
    return repos


def gh_list(path: str) -> list:
    out = subprocess.run(["gh", "api", "--paginate", "--slurp", path],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        lines = (out.stderr or out.stdout or "gh api failed").strip().splitlines()
        raise RuntimeError(lines[-1] if lines else "gh api failed")
    pages = json.loads(out.stdout)
    return [x for page in pages for x in page]


def fetch(repos: list[str]) -> tuple[dict, dict]:
    data, errors = {}, {}
    for repo in repos:
        try:
            data[repo] = {"issues": gh_list(f"repos/{repo}/issues?state=open&per_page=100"),
                          "pulls": gh_list(f"repos/{repo}/pulls?state=open&per_page=100")}
        except Exception as e:  # report per repo, keep going
            errors[repo] = str(e)
    return data, errors


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--registry", required=True, help="path to registry/repos.yml")
    p.add_argument("--json", action="store_true", help="print JSON instead of chat text")
    a = p.parse_args(argv)
    raw = sys.stdin.read().strip()
    try:
        inp = json.loads(raw) if raw else {}
    except json.JSONDecodeError as e:
        print(f"error: input is not valid JSON: {e}", file=sys.stderr)
        return 1
    data, errors = fetch(repos_to_read(a.registry))
    s = build(data, errors, inp.get("triggers"), inp.get("runner"), inp.get("usage"), int(time.time()))
    print(json.dumps(s, indent=2) if a.json else render(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
