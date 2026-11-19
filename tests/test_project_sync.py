"""Tests for the label -> Project Status mapping in scripts/project_sync.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from project_sync import STATUS_ORDER, managed_repos, ready_to_merge_issues, status_for  # noqa: E402


def issue(*labels, state="open", body="", number=1):
    return {"labels": [{"name": n} for n in labels], "state": state, "body": body, "number": number}


def pr(*labels, state="open", body=""):
    item = issue(*labels, state=state, body=body, number=99)
    item["pull_request"] = {}
    return item


def test_brief_without_triage_is_brief():
    assert status_for(issue("ai:brief")) == "Brief"


def test_triaged_brief_waiting_for_design_is_design():
    assert status_for(issue("ai:brief", "ai:triaged", "size:large", "ai:needs-design")) == "Design"


def test_draft_task():
    assert status_for(issue("size:small", "ai:draft", body="Parent: altaprimadev/claude-cowork#3")) == "Draft"


def test_needs_human_label_wins_over_other_labels():
    assert status_for(issue("ai:brief", "ai:triaged", "ai:needs-human")) == "In review"


def test_reviewed_task_without_stage_label_is_backlog():
    body = "<!-- ai:plan parent=altaprimadev/claude-cowork#3 task=2 -->\nParent: altaprimadev/claude-cowork#3"
    assert status_for(issue("size:large", body=body)) == "Backlog"


def test_closed_pipeline_issue_is_done():
    assert status_for(issue("ai:in-progress", state="closed")) == "Done"


def test_non_pipeline_issue_is_skipped():
    assert status_for(issue("bug")) is None


def test_report_and_pull_requests_are_skipped():
    assert status_for(issue("ai:report")) is None
    pr = issue("ai:review-passed")
    pr["pull_request"] = {}
    assert status_for(pr) is None


def test_every_label_status_has_an_option():
    from project_sync import LABEL_STATUS

    assert set(LABEL_STATUS.values()) | {"Done", "Backlog", "Ready to merge"} == set(STATUS_ORDER)


def test_task_with_review_passed_pr_is_ready_to_merge():
    items = [pr("ai:review-passed", body="Closes #7"), issue("ai:in-progress", number=7)]
    assert status_for(items[1], ready_to_merge_issues(items)) == "Ready to merge"


def test_needs_human_wins_over_ready_to_merge():
    items = [pr("ai:review-passed", body="Fixes #7"), issue("ai:needs-human", number=7)]
    assert status_for(items[1], ready_to_merge_issues(items)) == "In review"


def test_pr_without_review_passed_or_closed_is_ignored():
    items = [
        pr("ai:changes-needed", body="Closes #7"),
        pr("ai:review-passed", body="Resolves #8", state="closed"),
    ]
    assert ready_to_merge_issues(items) == set()


def test_closing_keywords():
    items = [pr("ai:review-passed", body="closes #3\nFixed #4, resolved #5. See #6.")]
    assert ready_to_merge_issues(items) == {3, 4, 5}


def test_managed_repos_keeps_control_repo_first_and_skips_inactive():
    registry = {"repos": [
        {"name": "o/control", "status": "active"},
        {"name": "o/api", "status": "active"},
        {"name": "o/legacy", "status": "frozen"},
        {"name": "o/new", "status": "onboarding"},
    ]}
    assert managed_repos(registry, "o/control") == ["o/control", "o/api"]
