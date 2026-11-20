"""Corpus tests for .claude/hooks/guard_bash.py.

- tests/fixtures/guard_bypass_block.txt: bypass probes. Each must be blocked.
- tests/fixtures/guard_bypass_allow.txt: commands the pipeline needs. Each must pass.
- Every ```bash / ```sh block in the skills, agents, and scheduled-task prompts
  must pass, so a stricter guard never breaks a documented pipeline step.

Run: python3 -m pytest tests/test_guard_bash_corpus.py -q
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "guard_bash.py"
FIXTURES = ROOT / "tests" / "fixtures"

# Documented blocks that must stay blocked on purpose. Path relative to ROOT.
DOC_BLOCKS_EXPECTED_BLOCKED: set[str] = set()


def load(name: str) -> list[str]:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    entries = re.split(r"^---$", text, flags=re.MULTILINE)
    out = []
    for e in entries:
        cmd = "\n".join(l for l in e.strip("\n").splitlines() if not l.startswith("#")).strip()
        if cmd:
            out.append(cmd)
    return out


def doc_blocks() -> list[tuple[str, str]]:
    files = sorted(ROOT.glob(".claude/skills/*/SKILL.md")) + sorted(ROOT.glob(".claude/agents/*.md"))
    files.append(ROOT / "docs" / "scheduled-tasks.md")
    out = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        for i, m in enumerate(re.finditer(r"^[ \t]*```(?:bash|sh)\n(.*?)^[ \t]*```", text, re.DOTALL | re.MULTILINE)):
            body = "\n".join(l.strip() for l in m.group(1).splitlines())
            out.append((f"{f.relative_to(ROOT)}#{i}", body))
    return out


def run(command: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GUARD_TEST_")}
    env["CLAUDE_PROJECT_DIR"] = str(ROOT)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                          text=True, env=env, cwd=str(ROOT), timeout=15)


@pytest.mark.parametrize("command", load("guard_bypass_block.txt"))
def test_bypass_probe_is_blocked(command):
    r = run(command)
    assert r.returncode == 2, f"not blocked: {command!r}\nstderr: {r.stderr}"
    assert "BLOCKED by .claude/hooks/guard_bash.py" in r.stderr


@pytest.mark.parametrize("command", load("guard_bypass_allow.txt"))
def test_pipeline_command_is_allowed(command):
    r = run(command)
    assert r.returncode == 0, f"blocked: {command!r}\nstderr: {r.stderr}"


@pytest.mark.parametrize("ref,block", doc_blocks(), ids=[r for r, _ in doc_blocks()])
def test_documented_block_is_allowed(ref, block):
    r = run(block)
    expected = 2 if ref in DOC_BLOCKS_EXPECTED_BLOCKED else 0
    assert r.returncode == expected, f"{ref}: exit {r.returncode}\nstderr: {r.stderr}\n---\n{block}"


def test_internal_error_fails_open(monkeypatch, capsys):
    import importlib.util
    import io

    spec = importlib.util.spec_from_file_location("guard_bash", HOOK)
    guard = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "guard_bash", guard)  # dataclasses look the module up
    spec.loader.exec_module(guard)

    def boom(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(guard, "evaluate", boom)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": "ls"}})))
    assert guard.main() == 0
    assert "internal error (RuntimeError: boom); allowing command" in capsys.readouterr().err


def test_corpus_is_not_empty():
    assert len(load("guard_bypass_block.txt")) >= 40
    assert len(doc_blocks()) >= 20
