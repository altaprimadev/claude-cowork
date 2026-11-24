#!/usr/bin/env python3
"""Check every pipeline setup step for the workflow-setup skill.

Read-only. The script probes GitHub with `gh api` (REST) and reads the
control repo files. The agent passes the data it reads through MCP tools on
stdin:

  {"triggers": <list_triggers data>,
   "runner": <get_session result of the runner session, or null>,
   "environments": <list_environments data, or null>,
   "org_repos": [<"owner/name" from list_repos>] or null,
   "runner_guard": "active" | "inactive" | null}

Each step has an owner: `human` (an action no AI session can do) or `ai`
(the wizard does it). Result: pass, fail (the state is wrong; reason), or
error (the check could not run; reason). The audit judges only against the
rules and docs of claude-cowork. It gives no advice: suggestions belong to
watchtower.

Usage:
  python3 setup_audit.py --root <claude-cowork clone> [--json] < input.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CONTROL_REPO = "alta-prima-indonesia/claude-cowork"
ORG = "alta-prima-indonesia"
TASKS = {
    "Pipeline: onboarding scan": {"section": "## 1. Onboarding scan",
                                  "cron": re.compile(r"^CRON_TZ=Asia/Jakarta 30 14 \* \* \*$")},
    "Pipeline: batch": {"section": "## 2. Batch",
                        "cron": re.compile(r"^\d{1,2} \* \* \* \*$")},
}
ENV_NAME = "altaprima-default"
ICON = {"pass": "✅", "fail": "❌", "error": "⚠️"}
LABEL_LINE = re.compile(r'^\s*"([^"|]+)\|([0-9a-fA-F]{6})\|([^"]*)"\s*$')
FENCE = re.compile(r"```text\n(.*?)\n```", re.DOTALL)
HTTP_CODE = re.compile(r"\(HTTP (\d{3})\)")


# ---------- inputs from the control repo ----------

def parse_labels(script_text: str) -> list[dict]:
    """Label specs from scripts/setup-labels.sh, the single source of the label list."""
    out = []
    for line in script_text.splitlines():
        m = LABEL_LINE.match(line)
        if m:
            out.append({"name": m.group(1), "color": m.group(2).lower(), "description": m.group(3)})
    return out


def parse_prompts(doc_text: str) -> dict[str, str]:
    """The first ```text block under each task section of docs/scheduled-tasks.md."""
    out = {}
    for name, spec in TASKS.items():
        start = doc_text.find(spec["section"])
        if start < 0:
            continue
        m = FENCE.search(doc_text, start)
        if m:
            out[name] = m.group(1).strip()
    return out


def load_registry(root: Path) -> list[dict]:
    import yaml
    data = yaml.safe_load((root / "registry" / "repos.yml").read_text()) or {}
    return list(data.get("repos") or [])


def load_policy(root: Path) -> dict:
    import yaml
    return yaml.safe_load((root / "registry" / "policy.yml").read_text()) or {}


# ---------- GitHub ----------

def gh(path: str) -> tuple[int, object]:
    """GET a REST path. Returns (HTTP status, JSON body or None)."""
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60)
    if out.returncode == 0:
        try:
            return 200, json.loads(out.stdout or "null")
        except json.JSONDecodeError:
            return 200, None
    m = HTTP_CODE.search(out.stderr or "")
    return (int(m.group(1)) if m else 0), None


def repo_of(url: str) -> str:
    m = re.search(r"github\.com[/:]([^/]+/[^/.]+)", url or "")
    return m.group(1) if m else ""


def unwrap(obj):
    """get_session results may come wrapped in {"ccr": {...}}."""
    if isinstance(obj, dict) and "ccr" in obj and isinstance(obj["ccr"], dict):
        return obj["ccr"]
    return obj


# ---------- steps ----------

def step(sid, owner, title, status, reason=""):
    """One audit result: pass, fail (state is wrong), or error (check could not run)."""
    return {"id": sid, "owner": owner, "title": title, "status": status, "reason": reason}


def check_labels(repos, specs, get):
    missing, unread = {}, []
    want = {s["name"] for s in specs}
    for r in repos:
        code, body = get(f"repos/{r}/labels?per_page=100")
        if code != 200 or not isinstance(body, list):
            unread.append(f"{r} (HTTP {code})")
            continue
        have = {x.get("name") for x in body}
        lack = sorted(want - have)
        if lack:
            missing[r] = lack
    if unread:
        return step("A2", "ai", "Label pipeline", "error", "nggak kebaca: " + ", ".join(unread))
    if missing:
        detail = "; ".join(f"{r}: {len(v)} kurang" for r, v in missing.items())
        return step("A2", "ai", "Label pipeline", "fail", detail)
    return step("A2", "ai", "Label pipeline", "pass", f"{len(want)} label di {len(repos)} repo")


def check_codeowners(repos, get):
    lack, unread = [], []
    for r in repos:
        code, _ = get(f"repos/{r}/contents/.github/CODEOWNERS")
        if code == 404:
            lack.append(r)
        elif code != 200:
            unread.append(f"{r} (HTTP {code})")
    if unread:
        return step("A3", "ai", "CODEOWNERS", "error", "nggak kebaca: " + ", ".join(unread))
    if lack:
        return step("A3", "ai", "CODEOWNERS", "fail", "belum ada di " + ", ".join(lack))
    return step("A3", "ai", "CODEOWNERS", "pass", f"ada di {len(repos)} repo")


def check_protection(entries, get):
    """Returns (plan step H1, protection step A4)."""
    plan_blocked, compensated, none, ok, unread = [], [], [], [], []
    for e in entries:
        r = e["name"]
        code, repo = get(f"repos/{r}")
        branch = (repo or {}).get("default_branch") if code == 200 else None
        if not branch:
            unread.append(f"{r} (HTTP {code})")
            continue
        code, _ = get(f"repos/{r}/branches/{branch}/protection")
        if code == 200:
            ok.append(r)
        elif code == 403:
            plan_blocked.append(r)
            if e.get("branch_protection") == "unavailable":
                compensated.append(r)
        elif code == 404:
            none.append(r)
        else:
            unread.append(f"{r} (HTTP {code})")
    if plan_blocked:
        h1 = step("H1", "human", "Paket GitHub Team untuk org", "fail",
                  "proteksi branch ditolak paket Free: " + ", ".join(plan_blocked))
    elif unread and not (ok or none):
        h1 = step("H1", "human", "Paket GitHub Team untuk org", "error", "nggak kebaca")
    else:
        h1 = step("H1", "human", "Paket GitHub Team untuk org", "pass", "proteksi branch tersedia")
    if unread:
        a4 = step("A4", "ai", "Proteksi branch / ruleset", "error", "nggak kebaca: " + ", ".join(unread))
    elif none:
        a4 = step("A4", "ai", "Proteksi branch / ruleset", "fail", "belum diproteksi: " + ", ".join(none))
    elif plan_blocked:
        detail = "nunggu H1"
        if compensated:
            detail += "; aturan kompensasi aktif di " + ", ".join(compensated)
        a4 = step("A4", "ai", "Proteksi branch / ruleset", "fail", detail)
    else:
        a4 = step("A4", "ai", "Proteksi branch / ruleset", "pass", f"{len(ok)} repo terproteksi")
    return h1, a4


def latest_run(get, workflow: str, branch: str = "main"):
    code, body = get(f"repos/{CONTROL_REPO}/actions/workflows/{workflow}/runs?branch={branch}&per_page=1")
    if code != 200 or not isinstance(body, dict):
        return code, None
    runs = body.get("workflow_runs") or []
    return code, (runs[0] if runs else None)


def check_ci(get):
    code, run = latest_run(get, "ci.yml")
    if code == 404:
        return step("A5", "ai", "CI validate di claude-cowork", "fail", "workflow ci.yml nggak ada")
    if code != 200:
        return step("A5", "ai", "CI validate di claude-cowork", "error", f"HTTP {code}")
    if not run:
        return step("A5", "ai", "CI validate di claude-cowork", "fail", "belum pernah jalan di main")
    concl = run.get("conclusion") or run.get("status")
    status = "pass" if concl == "success" else "fail"
    return step("A5", "ai", "CI validate di claude-cowork", status, f"run terakhir di main: {concl}")


def check_project(policy, get):
    """Returns (board step H5, token step H6, sync step A6)."""
    number = ((policy.get("project") or {}).get("number")) or 0
    h5 = step("H5", "human", "GitHub Project board", "pass" if number else "fail",
              f"project.number = {number}")
    run_code, run = latest_run(get, "project-sync.yml")
    synced = run_code == 200 and bool(number) and (run or {}).get("conclusion") == "success"
    code, _ = get(f"repos/{CONTROL_REPO}/actions/secrets/PROJECT_SYNC_TOKEN")
    if code == 200:
        h6 = step("H6", "human", "Token PROJECT_SYNC_TOKEN", "pass", "secret ada")
    elif code == 404:
        h6 = step("H6", "human", "Token PROJECT_SYNC_TOKEN", "fail", "secret belum ada")
    elif synced:
        h6 = step("H6", "human", "Token PROJECT_SYNC_TOKEN", "pass", "terbukti dari run project-sync yang sukses")
    else:
        h6 = step("H6", "human", "Token PROJECT_SYNC_TOKEN", "error", f"secret nggak kebaca (HTTP {code})")
    if not number or h6["status"] == "fail":
        return h5, h6, step("A6", "ai", "Project sync jalan", "fail", "nunggu H5/H6")
    if run_code != 200:
        return h5, h6, step("A6", "ai", "Project sync jalan", "error", f"HTTP {run_code}")
    concl = (run or {}).get("conclusion") or (run or {}).get("status") or "belum pernah jalan"
    status = "pass" if concl == "success" else "fail"
    return h5, h6, step("A6", "ai", "Project sync jalan", status, f"run terakhir: {concl}")


def check_env(environments):
    if environments is None:
        return step("H7", "human", "Cloud environment", "error", "list_environments nggak dikirim")
    names = [e.get("name") for e in environments if isinstance(e, dict)]
    if ENV_NAME in names:
        return step("H7", "human", "Cloud environment", "error",
                    f"{ENV_NAME} ada; network, setup script, dan env var cuma bisa dicek di UI")
    return step("H7", "human", "Cloud environment", "fail", f"{ENV_NAME} belum ada")


def check_managed(runner_guard):
    if runner_guard == "active":
        return step("H8", "human", "Managed settings org (hook + permission)", "pass",
                    "runner melapor guard: active")
    if runner_guard == "inactive":
        return step("H8", "human", "Managed settings org (hook + permission)", "fail",
                    "runner melapor guard: inactive")
    return step("H8", "human", "Managed settings org (hook + permission)", "error",
                "belum ada laporan guard dari runner")


def runner_id(triggers) -> str | None:
    ids = {t.get("persistent_session_id") for t in triggers or []
           if t.get("name") in TASKS and t.get("persistent_session_id")}
    return ids.pop() if len(ids) == 1 else None


def check_runner(runner, active, frozen):
    """Returns (runner step A7, attach step H9)."""
    r = unwrap(runner)
    if not r:
        return (step("A7", "ai", "Sesi runner", "fail", "belum ada runner yang terikat ke task"),
                step("H9", "human", "Pasang repo push + baris pr-watch di runner", "fail", "nunggu A7"))
    status = r.get("session_status") or ""
    if "ARCHIVED" in status:
        return (step("A7", "ai", "Sesi runner", "fail", "runner diarsipkan"),
                step("H9", "human", "Pasang repo push + baris pr-watch di runner", "fail", "nunggu A7"))
    a7 = step("A7", "ai", "Sesi runner", "pass", f"{r.get('id')} ({status.replace('SESSION_STATUS_', '').lower()})")
    sources = {repo_of(s.get("git_repository", {}).get("url", ""))
               for s in (r.get("session_context") or {}).get("sources") or []}
    lack = [x for x in active + frozen if x not in sources]
    if lack:
        h9 = step("H9", "human", "Pasang repo push + baris pr-watch di runner", "fail",
                  "repo belum terpasang: " + ", ".join(lack))
    else:
        h9 = step("H9", "human", "Pasang repo push + baris pr-watch di runner", "error",
                  "semua repo terpasang; baris pr-watch nggak bisa dicek dari luar")
    return a7, h9


def check_tasks(triggers, prompts, rid):
    by_name = {t.get("name"): t for t in triggers or []}
    problems = []
    for name, spec in TASKS.items():
        t = by_name.get(name)
        if not t:
            problems.append(f"{name}: belum ada")
            continue
        if not t.get("enabled", False):
            problems.append(f"{name}: nonaktif")
        if rid and t.get("persistent_session_id") != rid:
            problems.append(f"{name}: terikat ke sesi lain")
        if not spec["cron"].match((t.get("cron_expression") or "").strip()):
            problems.append(f"{name}: jadwal {t.get('cron_expression')!r} beda dari docs")
        stored = ((t.get("derived_state") or {}).get("prompt") or t.get("prompt") or "").strip()
        if name in prompts and stored != prompts[name]:
            problems.append(f"{name}: prompt beda dari docs")
    if problems:
        return step("A8", "ai", "Scheduled task pipeline", "fail", "; ".join(problems))
    return step("A8", "ai", "Scheduled task pipeline", "pass", "2 task aktif, prompt sama dengan docs")


def check_registry(org_repos, entries):
    if org_repos is None:
        return step("A9", "ai", "Registry vs repo org", "error", "list_repos nggak dikirim")
    known = {e["name"] for e in entries}
    detected = sorted(r for r in org_repos if r.startswith(ORG + "/") and r not in known)
    if detected:
        return step("A9", "ai", "Registry vs repo org", "fail", "belum di registry: " + ", ".join(detected))
    return step("A9", "ai", "Registry vs repo org", "pass", "semua repo org ada di registry")


def check_settings_sync(root: Path, run=subprocess.run):
    out = run([sys.executable, str(root / "scripts" / "validate-config.py"), str(root)],
              capture_output=True, text=True, timeout=120)
    if out.returncode == 0:
        return step("A1", "ai", "Config repo valid (settings = template)", "pass", "validate-config OK")
    last = [x.strip() for x in ((out.stdout or "") + (out.stderr or "")).splitlines() if x.strip()]
    return step("A1", "ai", "Config repo valid (settings = template)", "fail",
                last[-1] if last else "validate-config gagal")


def check_github_login(get):
    code, body = get("user")
    if code == 200 and isinstance(body, dict):
        login = body.get("login", "?")
        return step("H4", "human", "GitHub tersambung + Claude GitHub App", "pass", f"gh login: {login}")
    return step("H4", "human", "GitHub tersambung + Claude GitHub App", "fail", f"gh api user: HTTP {code}")


def build(data: dict, root: Path, get=gh, run=subprocess.run) -> dict:
    entries = load_registry(root)
    policy = load_policy(root)
    active = [e["name"] for e in entries if e.get("status") == "active"]
    frozen = [e["name"] for e in entries if e.get("status") == "frozen"]
    specs = parse_labels((root / "scripts" / "setup-labels.sh").read_text())
    prompts = parse_prompts((root / "docs" / "scheduled-tasks.md").read_text())
    triggers = data.get("triggers") or []
    rid = runner_id(triggers)
    active_entries = [e for e in entries if e.get("status") == "active"]

    h1, a4 = check_protection(active_entries, get)
    h5, h6, a6 = check_project(policy, get)
    a7, h9 = check_runner(data.get("runner"), active, frozen)
    steps = [
        h1,
        step("H2", "human", "Paket dan akun Claude untuk agen", "error",
             "pembayaran dan seat nggak bisa dicek dari sesi"),
        step("H3", "human", "Akun GitHub machine user + 2FA", "error",
             "pembuatan akun dan 2FA nggak bisa dicek dari sesi"),
        check_github_login(get),
        h5, h6,
        check_env(data.get("environments")),
        check_managed(data.get("runner_guard")),
        h9,
        check_settings_sync(root, run),
        check_labels([CONTROL_REPO] + [r for r in active if r != CONTROL_REPO], specs, get),
        check_codeowners(active, get),
        a4,
        check_ci(get),
        a6, a7,
        check_tasks(triggers, prompts, rid),
        check_registry(data.get("org_repos"), entries),
    ]
    counts = {}
    for s in steps:
        counts[s["status"]] = counts.get(s["status"], 0) + 1
    return {"runner_session_id": rid, "steps": steps, "counts": counts}


def render(result: dict) -> str:
    lines = []
    for owner, title in (("human", "Langkah manusia"), ("ai", "Langkah AI (wizard)")):
        lines.append(f"**{title}**")
        lines.append("")
        lines.append("| ID | Langkah | Hasil | Alasan |")
        lines.append("|---|---|---|---|")
        for s in result["steps"]:
            if s["owner"] != owner:
                continue
            reason = "-" if s["status"] == "pass" else (s["reason"] or "-")
            lines.append(f"| {s['id']} | {s['title']} | {ICON[s['status']]} {s['status']} | {reason} |")
        lines.append("")
    c = result["counts"]
    lines.append("Ringkasan: " + ", ".join(f"{k} {c[k]}" for k in ("pass", "fail", "error") if k in c))
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--root", required=True, help="claude-cowork clone")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    raw = sys.stdin.read().strip()
    data = json.loads(raw) if raw else {}
    result = build(data, Path(a.root))
    print(json.dumps(result, indent=2, ensure_ascii=False) if a.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
