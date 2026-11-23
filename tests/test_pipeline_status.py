"""Tests for .claude/skills/pipeline-status/scripts/status.py."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "pipeline-status" / "scripts"))

from status import build, classify, render, runner_state  # noqa: E402

REPO = "alta-prima-indonesia/svc"
NOW = 1795150000  # 2026-11-20T03:26:40Z


def issue(n, labels=(), body="", updated="2026-11-20T03:00:00Z", pr=False):
    it = {"number": n, "title": f"item {n}", "html_url": f"https://x/{n}",
          "labels": [{"name": l} for l in labels], "body": body, "updated_at": updated}
    if pr:
        it["pull_request"] = {}
    return it


def pull(n, head, body=""):
    return {"number": n, "head": {"ref": head}, "body": body}


def data(issues, pulls=()):
    return {REPO: {"issues": list(issues), "pulls": list(pulls)}}


def test_groups_follow_labels_and_branches():
    d = data(
        [issue(1, ["ai:in-progress"]),
         issue(2, ["ai:in-progress"]),
         issue(10, pr=True), issue(11, ["ai:review-passed"], pr=True), issue(12, pr=True),
         issue(13, ["ai:changes-needed"], pr=True),
         issue(3, ["ai:ready"]), issue(4, ["ai:draft"]), issue(5, ["ai:needs-human"]),
         issue(6, ["ai:report"])],
        [pull(10, "ai/1-x", "Closes #1"), pull(11, "ai/7-y"), pull(12, "design/8-z"), pull(13, "ai/9-w")])
    g = classify(d, NOW)
    nums = {k: [i["number"] for i in v] for k, v in g.items() if v}
    assert nums == {"working": [2], "agent_review": [10], "merge": [11, 12], "fix_queue": [13],
                    "ready": [3], "draft": [4], "human": [5]}
    assert [i["gate"] for i in g["merge"]] == ["Gate 2 (code)", "Gate 1 (design)"]


def test_stale_in_progress_without_pr():
    g = classify(data([issue(1, ["ai:in-progress"], updated="2026-11-18T00:00:00Z")]), NOW)
    assert g["stale"][0]["idle_hours"] >= 24 and not g["working"]


def test_planned_task_lists_open_dependencies_only():
    body = "<!-- ai:plan parent=a/b#1 task=2 -->\nParent: a/b#1\nDepends on: alta-prima-indonesia/svc#20, #21"
    g = classify(data([issue(22, body=body), issue(20, ["ai:in-progress"])]), NOW)
    assert g["waiting_deps"][0]["deps"] == ["alta-prima-indonesia/svc#20"]


def test_next_heavy_respects_usage_and_busy_repos():
    d = data([issue(1, ["ai:in-progress"]), issue(3, ["ai:ready"])])
    assert "nggak ada: repo" in build(d, {}, None, None, None, NOW)["next_heavy"]
    assert "caution" in build(d, {}, None, None, {"advice": "caution"}, NOW)["next_heavy"]
    d = data([issue(3, ["ai:ready"])])
    assert build(d, {}, None, None, {"advice": "proceed"}, NOW)["next_heavy"] == "implementasi svc#3 (kandidat)"


def test_render_shows_runner_schedule_and_usage():
    runner = {"ccr": {"id": "session_1", "title": "Runner", "status_bucket": "SESSION_STATUS_BUCKET_WORKING",
                      "task_summary": "Review PR 67"}}
    triggers = {"data": [{"name": "Pipeline: batch", "enabled": True, "next_run_at": "2026-11-20T07:37:39Z"},
                         {"name": "Usage reset reminder", "enabled": True, "next_run_at": "2026-11-20T08:31:00Z"}]}
    usage = {"advice": "proceed", "windows": {"five_hour": {"usage_percent": 40},
                                               "seven_day": {"usage_percent": 60}}}
    out = render(build(data([issue(3, ["ai:ready"])]), {"a/b": "HTTP 403"}, triggers, runner, usage, NOW))
    assert "lagi jalan: Review PR 67" in out
    assert "Pipeline: batch: berikutnya 2026-11-20 14:37 WIB" in out
    assert "Usage reset reminder" not in out
    assert "**Antrian run berikutnya** (1)" in out
    assert "- a/b: HTTP 403" in out
    assert out.endswith("usage: 5h 40%, weekly 60%, advice proceed")


def test_unplanned_task_without_stage_label_is_not_promoted():
    small = issue(30, body="Parent: alta-prima-indonesia/claude-cowork#5\nTrivial: no")
    planned = issue(31, body="<!-- ai:plan parent=a/b#1 task=1 -->\nParent: a/b#1\nDepends on: none")
    out = render(build(data([small, planned]), {}, None, None, None, NOW))
    assert "svc#30" in out and "tanpa label stage" in out
    assert "di-promote run berikutnya" in out.split("svc#31", 1)[1].split("\n", 1)[0]


def test_runner_state_falls_back_to_session_status():
    assert runner_state({"id": "s1", "session_status": "SESSION_STATUS_IDLE"})["state"] == "idle"
    assert runner_state({"id": "s1", "session_status": "SESSION_STATUS_PENDING"})["state"] == "working"
    assert runner_state({"id": "s1", "session_status": "SESSION_STATUS_OTHER"})["state"] == "unknown"
    both = {"id": "s1", "status_bucket": "SESSION_STATUS_BUCKET_FAILED", "session_status": "SESSION_STATUS_IDLE"}
    assert runner_state(both)["state"] == "failed"
