"""Tests for .claude/skills/usage-reminder/scripts/reminder.py."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "usage-reminder" / "scripts"))

from reminder import active_repos, classify, main, next_fire  # noqa: E402

NOW = 1795080600  # 2026-11-19T09:30:00Z


def item(n, *labels, pr=False):
    it = {"number": n, "title": f"t{n}", "html_url": f"u{n}",
          "labels": [{"name": l} for l in labels]}
    if pr:
        it["pull_request"] = {}
    return it


def test_first_matching_group_wins():
    groups = classify([item(1, "ai:in-progress", "ai:needs-human"), item(2, "ai:ready")])
    assert [i["number"] for i in groups["needs_human"]] == [1]
    assert "in_progress" not in groups
    assert [i["number"] for i in groups["ready"]] == [2]


def test_triaged_brief_and_reports_are_not_tasks():
    groups = classify([item(1, "ai:brief", "ai:triaged"), item(2, "ai:report"), item(3, "bug")])
    assert groups == {}


def test_new_brief_and_prs_are_grouped():
    groups = classify([item(1, "ai:brief"), item(2, "ai:review-passed", pr=True), item(3, pr=True)])
    assert list(groups) == ["review_passed", "new_brief", "open_pr"]


def test_next_fire_is_reset_plus_one_minute():
    usage = {"windows": {"five_hour": {"resets_at_iso": "2026-11-19T12:30:00Z"}}}
    at, source = next_fire(usage, NOW)
    assert source == "reset"
    assert at == NOW + 3 * 3600 + 60


def test_next_fire_falls_back_when_data_missing_or_stale():
    stale = {"windows": {"five_hour": {"resets_at_iso": "2026-11-19T09:00:00Z"}}}
    assert next_fire(stale, NOW) == (NOW + 5 * 3600, "fallback")
    assert next_fire(None, NOW) == (NOW + 5 * 3600, "fallback")


def test_next_fire_cli_prints_iso(capsys, monkeypatch):
    import io
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert main(["next-fire", "--now", str(NOW)]) == 0
    assert json.loads(capsys.readouterr().out) == {"at": "2026-11-19T14:30:00Z", "source": "fallback"}


def test_active_repos_reads_only_active(tmp_path):
    reg = tmp_path / "repos.yml"
    reg.write_text("repos:\n  - {name: a/x, status: active}\n  - {name: a/y, status: frozen}\n")
    assert active_repos(str(reg)) == ["a/x"]
