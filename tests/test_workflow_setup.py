"""Tests for .claude/skills/workflow-setup/scripts/setup_audit.py."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "workflow-setup" / "scripts"))

import setup_audit as audit  # noqa: E402

CONTROL = "alta-prima-indonesia/claude-cowork"
BACK = "alta-prima-indonesia/alta-prima-admin-back-end"
RUNNER = "session_runner"


def prompts():
    return audit.parse_prompts((ROOT / "docs" / "scheduled-tasks.md").read_text())


def labels():
    return audit.parse_labels((ROOT / "scripts" / "setup-labels.sh").read_text())


def triggers(**over):
    p = prompts()
    base = [
        {"name": "Pipeline: batch", "enabled": True, "cron_expression": "54 * * * *",
         "persistent_session_id": RUNNER, "derived_state": {"prompt": p["Pipeline: batch"]}},
        {"name": "Pipeline: onboarding scan", "enabled": True,
         "cron_expression": "CRON_TZ=Asia/Jakarta 30 14 * * *",
         "persistent_session_id": RUNNER, "derived_state": {"prompt": p["Pipeline: onboarding scan"]}},
    ]
    for t in base:
        t.update(over.get(t["name"], {}))
    return base


def fake_gh(routes):
    """routes: path prefix -> (code, body). Unknown paths return 404."""
    def get(path):
        for prefix, val in routes.items():
            if path.startswith(prefix):
                return val
        return 404, None
    return get


def ok_run(*_a, **_k):
    return subprocess.CompletedProcess([], 0, "OK", "")


def by_id(result):
    return {s["id"]: s for s in result["steps"]}


def test_parse_labels_and_prompts_from_repo_files():
    names = [x["name"] for x in labels()]
    assert "ai:brief" in names and "size:large" in names
    assert all(len(x["color"]) == 6 for x in labels())
    p = prompts()
    assert set(p) == {"Pipeline: batch", "Pipeline: onboarding scan"}
    assert p["Pipeline: batch"].startswith("You are the orchestrator")
    assert "```" not in p["Pipeline: batch"]


def test_tasks_done_when_prompts_match_and_bound_to_one_runner():
    s = audit.check_tasks(triggers(), prompts(), audit.runner_id(triggers()))
    assert s["status"] == "pass"


def test_tasks_report_drift_disabled_missing_and_rebind():
    t = triggers(**{"Pipeline: batch": {"enabled": False, "derived_state": {"prompt": "old"}},
                    "Pipeline: onboarding scan": {"persistent_session_id": "other"}})
    s = audit.check_tasks(t, prompts(), RUNNER)
    assert s["status"] == "fail"
    assert "nonaktif" in s["reason"] and "prompt beda" in s["reason"] and "sesi lain" in s["reason"]
    s = audit.check_tasks(triggers()[:1], prompts(), RUNNER)
    assert "onboarding scan: belum ada" in s["reason"]


def test_runner_id_needs_one_shared_session():
    assert audit.runner_id(triggers()) == RUNNER
    split = triggers(**{"Pipeline: batch": {"persistent_session_id": "other"}})
    assert audit.runner_id(split) is None


def test_runner_missing_blocks_h9_and_missing_repo_is_todo():
    a7, h9 = audit.check_runner(None, [CONTROL, BACK], [])
    assert a7["status"] == "fail" and h9["status"] == "fail"
    runner = {"ccr": {"id": RUNNER, "session_status": "SESSION_STATUS_IDLE",
                      "session_context": {"sources": [
                          {"git_repository": {"url": f"https://github.com/{CONTROL}"}}]}}}
    a7, h9 = audit.check_runner(runner, [CONTROL, BACK], [])
    assert a7["status"] == "pass"
    assert h9["status"] == "fail" and BACK in h9["reason"]


def test_protection_403_blocks_on_plan_and_404_is_ai_work():
    entries = [{"name": BACK, "branch_protection": "unavailable"}]
    get = fake_gh({f"repos/{BACK}/branches": (403, None), f"repos/{BACK}": (200, {"default_branch": "main"})})
    h1, a4 = audit.check_protection(entries, get)
    assert h1["status"] == "fail" and a4["status"] == "fail"
    assert "kompensasi" in a4["reason"]
    get = fake_gh({f"repos/{BACK}/branches": (404, None), f"repos/{BACK}": (200, {"default_branch": "main"})})
    h1, a4 = audit.check_protection(entries, get)
    assert h1["status"] == "pass" and a4["status"] == "fail"


def test_labels_missing_and_unreadable():
    specs = labels()
    get = fake_gh({f"repos/{CONTROL}/labels": (200, [{"name": "ai:brief"}])})
    s = audit.check_labels([CONTROL], specs, get)
    assert s["status"] == "fail"
    s = audit.check_labels([BACK], specs, fake_gh({f"repos/{BACK}/labels": (403, None)}))
    assert s["status"] == "error" and "403" in s["reason"]


def test_project_token_proven_by_successful_sync():
    policy = {"project": {"number": 2}}
    run = (200, {"workflow_runs": [{"conclusion": "success"}]})
    get = fake_gh({f"repos/{CONTROL}/actions/workflows/project-sync.yml": run,
                   f"repos/{CONTROL}/actions/secrets": (403, None)})
    h5, h6, a6 = audit.check_project(policy, get)
    assert (h5["status"], h6["status"], a6["status"]) == ("pass", "pass", "pass")
    h5, h6, a6 = audit.check_project({"project": {"number": 0}}, get)
    assert h5["status"] == "fail" and a6["status"] == "fail"


def test_registry_detects_new_org_repo_only():
    entries = [{"name": CONTROL}, {"name": BACK}]
    s = audit.check_registry([CONTROL, BACK, "alta-prima-indonesia/new-app", "someone/else"], entries)
    assert s["status"] == "fail" and "new-app" in s["reason"] and "else" not in s["reason"]
    assert audit.check_registry(None, entries)["status"] == "error"


def test_build_and_render_cover_every_step_owner():
    get = fake_gh({"user": (200, {"login": "bot"})})
    result = audit.build({"triggers": triggers(), "runner_guard": "active"}, ROOT, get=get, run=ok_run)
    ids = by_id(result)
    assert {f"H{i}" for i in range(1, 10)} <= set(ids)
    assert {f"A{i}" for i in range(1, 10)} <= set(ids)
    assert ids["H8"]["status"] == "pass" and ids["A1"]["status"] == "pass"
    assert ids["A8"]["status"] == "pass"
    text = audit.render(result)
    assert "**Langkah manusia**" in text and "**Langkah AI (wizard)**" in text
    assert text.strip().splitlines()[-1].startswith("Ringkasan:")


def test_guide_lists_every_human_step():
    guide = (ROOT / ".claude" / "skills" / "workflow-setup" / "references" / "human-guide.md").read_text()
    for i in range(1, 10):
        assert f"## H{i}." in guide


def test_audit_reports_only_pass_fail_error_without_advice():
    get = fake_gh({"user": (200, {"login": "bot"})})
    result = audit.build({"triggers": triggers()}, ROOT, get=get, run=ok_run)
    assert {s["status"] for s in result["steps"]} <= {"pass", "fail", "error"}
    assert all(set(s) == {"id", "owner", "title", "status", "reason"} for s in result["steps"])
    text = audit.render(result)
    assert "Berikutnya" not in text and "wizard W" not in text
    for row in text.splitlines():
        if "✅ pass" in row:
            assert row.rstrip().endswith("| - |")
