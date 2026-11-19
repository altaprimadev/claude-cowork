"""Tests for .claude/skills/skills-help/scripts/list_skills.py."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "skills-help" / "scripts"))

from list_skills import collect, first_sentence, main, render  # noqa: E402

CLAUDE_MD = """## Stage map

| Stage | Trigger | Agent | Skill(s) |
|---|---|---|---|
| Intake | New issue | `intake-triager` | `intake-classify` + stack packs |

Human-invoked skills run only in interactive sessions. Use them when a human asks:
- `inbox`: list what waits on the human.
Stack packs are listed in the profile.
"""


def make_repo(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(CLAUDE_MD)
    for name, desc, hint in [("inbox", "Show the inbox. More text.", "[repo]"),
                             ("intake-classify", "Triage one brief.", None),
                             ("stack-x", "Rules for X.", None),
                             ("usage-status", "Report usage.", None)]:
        d = tmp_path / ".claude" / "skills" / name
        d.mkdir(parents=True)
        fm = f"name: {name}\ndescription: {desc}\n" + (f'argument-hint: "{hint}"\n' if hint else "")
        (d / "SKILL.md").write_text(f"---\n{fm}---\n# {name}\n")
    return tmp_path


def test_groups_come_from_claude_md_and_names(tmp_path):
    groups = {s["name"]: s["group"] for s in collect(make_repo(tmp_path))}
    assert groups == {"inbox": "human", "intake-classify": "pipeline",
                      "stack-x": "pack", "usage-status": "utility"}


def test_render_orders_groups_and_shows_first_sentence(tmp_path):
    out = render(collect(make_repo(tmp_path)))
    assert out.index("Human-invoked") < out.index("Pipeline") < out.index("Utilities") < out.index("Stack packs")
    assert "- /inbox [repo]: Show the inbox." in out
    assert "More text" not in out


def test_one_skill_shows_full_description(tmp_path, capsys):
    assert main(["--root", str(make_repo(tmp_path)), "/inbox"]) == 0
    assert "Show the inbox. More text." in capsys.readouterr().out


def test_unknown_skill_fails(tmp_path, capsys):
    assert main(["--root", str(make_repo(tmp_path)), "nope"]) == 1
    assert "no skill named nope" in capsys.readouterr().err


def test_first_sentence_keeps_inner_dots():
    assert first_sentence("Uses app.request() here. Next.") == "Uses app.request() here."


def test_every_repo_skill_is_listed():
    names = {s["name"] for s in collect(ROOT)}
    on_disk = {p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md")}
    assert names == on_disk
