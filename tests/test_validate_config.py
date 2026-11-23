"""Tests for scripts/validate-config.py: settings and managed settings template stay in sync."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate-config.py"


def copy_repo(tmp_path: Path) -> Path:
    dst = tmp_path / "repo"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__"))
    return dst


def run(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)


def edit(path: Path, fn) -> None:
    data = json.loads(path.read_text())
    fn(data)
    path.write_text(json.dumps(data, indent=2) + "\n")


def test_repo_settings_match_the_template():
    assert run(ROOT).returncode == 0


def test_allow_rule_missing_from_template_fails(tmp_path):
    root = copy_repo(tmp_path)
    edit(root / "templates" / "managed-settings.json",
         lambda d: d["permissions"]["allow"].remove("Bash(git *)"))
    out = run(root)
    assert out.returncode == 1
    assert "Bash(git *)" in out.stdout


def test_allow_rule_missing_from_repo_settings_fails(tmp_path):
    root = copy_repo(tmp_path)
    edit(root / ".claude" / "settings.json",
         lambda d: d["permissions"]["allow"].remove("mcp__claude-code-remote__send_message"))
    out = run(root)
    assert out.returncode == 1
    assert "mcp__claude-code-remote__send_message" in out.stdout


def test_repo_only_deny_rules_may_stay_out_of_the_template(tmp_path):
    root = copy_repo(tmp_path)
    tpl = json.loads((root / "templates" / "managed-settings.json").read_text())
    assert "mcp__github__push_files" not in tpl["permissions"]["deny"]
    assert run(root).returncode == 0
