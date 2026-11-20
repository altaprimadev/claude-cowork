"""Tests for .claude/skills/usage-status/scripts/usage_status.py."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "usage-status" / "scripts"))

from usage_status import build, load_thresholds, render  # noqa: E402

RESET_5H = 1795091400
RESET_7D = 1795327200
NOW = RESET_5H - 90 * 60  # 1h30m before the five-hour reset


def info(five, seven=None, status="allowed", five_status="allowed"):
    windows = {"five_hour": {"resetsAt": RESET_5H, "status": five_status, "utilization": five}}
    if seven is not None:
        windows["seven_day"] = {"resetsAt": RESET_7D, "status": "allowed", "utilization": seven}
    return {"status": status, "unifiedWindows": windows}


def events(*infos):
    """Wrap rate_limit_info objects like a list_events response, oldest first."""
    return {"ccr": {"data": [
        {"created_at": f"2026-11-19T08:0{i}:00Z",
         "rate_limit_event": {"internal_anthropic_catchall": {"rate_limit_info": x}}}
        for i, x in enumerate(infos)
    ]}}


def test_renders_the_two_window_format():
    out = render(build(info(0.29, 0.70), NOW, 70, 90))
    assert out == "remaining hour to reset: 1h30m\nusage percentage:\n- 5h: 29%\n- weekly: 70%"


def test_uses_the_newest_event_and_its_capture_time():
    result = build(events(info(0.27, 0.35), info(0.33, 0.36)), NOW, 70, 90)
    assert result["windows"]["five_hour"]["usage_percent"] == 33
    assert result["captured_at"] == "2026-11-19T08:01:00Z"


@pytest.mark.parametrize("five,seven,expected", [
    (0.33, 0.36, "proceed"),
    (0.70, 0.10, "caution"),
    (0.89, 0.10, "caution"),
    (0.90, 0.10, "pause"),
    (0.10, 0.92, "proceed"),  # weekly percent is ignored
    (0.10, 0.75, "proceed"),
])
def test_overall_advice_follows_the_five_hour_window(five, seven, expected):
    assert build(info(five, seven), NOW, 70, 90)["advice"] == expected


def test_reached_weekly_limit_still_pauses():
    data = info(0.10, 1.0)
    data["unifiedWindows"]["seven_day"]["status"] = "rejected"
    assert build(data, NOW, 70, 90)["advice"] == "pause"


def test_rejected_status_pauses_and_is_printed():
    result = build(info(1.0, five_status="rejected", status="rejected"), NOW, 70, 90)
    assert result["advice"] == "pause"
    assert render(result).endswith("status: limit reached (5h)")


def test_window_past_reset_counts_as_zero_and_allowed():
    result = build(info(0.95, five_status="rejected"), RESET_5H + 60, 70, 90)
    w = result["windows"]["five_hour"]
    assert (w["usage_percent"], w["status"], w["advice"]) == (0, "allowed", "proceed")


def test_status_line_shape_is_accepted():
    data = {"rate_limits": {"five_hour": {"used_percentage": 23.5, "resets_at": RESET_5H}}}
    assert build(data, NOW, 70, 90)["windows"]["five_hour"]["usage_percent"] == 24


def test_no_data_raises():
    with pytest.raises(ValueError, match="no rate-limit data"):
        build({"ccr": {"data": []}}, NOW, 70, 90)


def test_thresholds_come_from_policy_file(tmp_path):
    policy = tmp_path / "policy.yml"
    policy.write_text("usage_budget:\n  caution_pct: 60\n  pause_pct: 80\n")
    assert load_thresholds(str(policy)) == (60, 80)


def test_repo_policy_defines_usage_budget():
    import yaml
    budget = yaml.safe_load((ROOT / "registry" / "policy.yml").read_text())["usage_budget"]
    assert 0 < budget["caution_pct"] < budget["pause_pct"] <= 100


def test_custom_thresholds_change_advice():
    assert build(info(0.65), NOW, 60, 80)["advice"] == "caution"


def test_invalid_thresholds_exit(tmp_path):
    bad = tmp_path / "policy.yml"
    bad.write_text("usage_budget:\n  caution_pct: 95\n  pause_pct: 90\n")
    with pytest.raises(SystemExit):
        load_thresholds(str(bad))
