"""Tests for .claude/hooks/pre_compact.py."""

import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "pre_compact.py"


def run(stdin: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, check=False)


def test_prints_the_instructions_and_never_blocks():
    result = run('{"hook_event_name": "PreCompact", "trigger": "auto"}')
    assert result.returncode == 0
    assert "keep only the latest" in result.stdout
    assert "[UNCERTAIN]" in result.stdout
    assert "Never turn an assumption into a fact" in result.stdout


def test_empty_input_still_exits_zero():
    assert run("").returncode == 0
