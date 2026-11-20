"""Tests for .claude/skills/watchtower/scripts/audit.py."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "watchtower" / "scripts"))

import audit  # noqa: E402


def clone(tmp_path):
    """Copy the parts of this repo the audit reads."""
    for part in (".claude", "docs", "scripts", "registry", "templates", "tests", ".github"):
        shutil.copytree(ROOT / part, tmp_path / part, ignore=shutil.ignore_patterns("__pycache__"))
    for f in ("CLAUDE.md", "README.md"):
        shutil.copy(ROOT / f, tmp_path / f)
    return tmp_path


def messages(findings, area):
    return [f["message"] for f in findings if f["area"] == area]


def test_repo_has_no_errors():
    findings = audit.run(ROOT)
    assert [f for f in findings if f["severity"] == "error"] == []


def test_unknown_label_is_an_error_but_markers_are_not(tmp_path):
    root = clone(tmp_path)
    skill = root / ".claude" / "skills" / "inbox" / "SKILL.md"
    skill.write_text(skill.read_text() + "\nSet `ai:waiting` here. Keep `<!-- ai:plan x=1 -->`.\n")
    msgs = messages(audit.run(root, "rules"), "rules")
    assert any("ai:waiting" in m for m in msgs)
    assert not any("ai:plan" in m for m in msgs)


def test_missing_policy_key_and_skill_script(tmp_path):
    root = clone(tmp_path)
    skill = root / ".claude" / "skills" / "inbox" / "SKILL.md"
    skill.write_text(skill.read_text().replace(
        "## Procedure", "## Procedure\n\nRead `max_widgets` from registry/policy.yml. Run scripts/nope.py.", 1))
    assert any("max_widgets" in m for m in messages(audit.run(root, "rules"), "rules"))
    assert any("scripts/nope.py" in m for m in messages(audit.run(root, skill="inbox"), "skills"))


def test_restated_fix_cap_is_an_error(tmp_path):
    root = clone(tmp_path)
    skill = root / ".claude" / "skills" / "inbox" / "SKILL.md"
    skill.write_text(skill.read_text() + "\nStop when rounds exceed `max_fix_attempts`.\n")
    msgs = messages(audit.run(root, "rules"), "rules")
    assert any("max_fix_attempts comparison" in m for m in msgs)
    skill.write_text(skill.read_text().replace(
        "exceed `max_fix_attempts`.", "exceed `max_fix_attempts` (CLAUDE.md -> \"Stop cleanly\")."))
    assert not any("max_fix_attempts comparison" in m for m in messages(audit.run(root, "rules"), "rules"))


def test_stage_skill_adding_needs_human_is_an_error(tmp_path):
    root = clone(tmp_path)
    skill = root / ".claude" / "skills" / "tdd" / "SKILL.md"
    skill.write_text(skill.read_text() + "\n- Something odd: comment, add `ai:needs-human`, stop.\n")
    assert any("adds ai:needs-human" in m for m in messages(audit.run(root, "rules"), "rules"))


def test_tag_pinned_action_and_pr_watch_without_finally(tmp_path):
    root = clone(tmp_path)
    wf = root / ".github" / "workflows" / "ci.yml"
    wf.write_text(wf.read_text().replace(
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0", "actions/checkout@v4"))
    watch = root / ".claude" / "skills" / "pr-watch" / "SKILL.md"
    watch.write_text(watch.read_text().replace("Finally", "closing"))
    msgs = messages(audit.run(root, "workflows"), "workflows")
    assert any("pin a full commit SHA" in m for m in msgs)
    assert any("Finally" in m for m in msgs)


def test_copied_policy_value_is_a_warning(tmp_path):
    root = clone(tmp_path)
    skill = root / ".claude" / "skills" / "inbox" / "SKILL.md"
    skill.write_text(skill.read_text() + "\nPause at 90% of the window.\n")
    msgs = messages(audit.run(root, "rules"), "rules")
    assert any("policy key `pause_pct`" in m for m in msgs)


def test_hook_gap_and_mcp_deny(tmp_path):
    root = clone(tmp_path)
    hook = root / ".claude" / "hooks" / "guard_bash.py"
    hook.write_text("import sys\nsys.exit(0)\n")  # a hook that blocks nothing
    settings = root / ".claude" / "settings.json"
    data = json.loads(settings.read_text())
    data["permissions"]["deny"] = [d for d in data["permissions"]["deny"] if "merge_pull_request" not in d]
    settings.write_text(json.dumps(data))
    msgs = messages(audit.run(root, "hooks"), "hooks")
    assert any("gh pr merge" in m for m in msgs)
    assert any("HEAD:main" in m for m in msgs)
    assert any("mcp__github__merge_pull_request" in m for m in msgs)


def test_consistency_flags_unlisted_human_skill_and_missing_path(tmp_path):
    root = clone(tmp_path)
    d = root / ".claude" / "skills" / "foo"
    d.mkdir()
    d.joinpath("SKILL.md").write_text(
        "---\nname: foo\ndescription: Do foo. Use when a human in an interactive session asks for foo.\n---\n"
        "# Foo\n\nSee `docs/missing.md`.\n")
    msgs = messages(audit.run(root, "consistency"), "consistency")
    assert any("foo is not in the human-invoked list" in m for m in msgs)
    assert any("no entry for skill foo" in m for m in msgs)


def test_slash_command_without_skill(tmp_path):
    root = clone(tmp_path)
    doc = root / "docs" / "setup.md"
    doc.write_text(doc.read_text() + "\nRun `/nosuch` then `/loop`.\n")
    msgs = messages(audit.run(root, "workflows"), "workflows")
    assert msgs.count("slash command /nosuch has no skill") == 1
    assert not any("/loop" in m for m in msgs)


def test_render_and_exit_code(capsys):
    assert audit.main(["--root", str(ROOT), "--area", "rules"]) == 0
    assert capsys.readouterr().out.startswith("watchtower: 0 error")
    assert audit.main(["--root", str(ROOT), "--skill", "nosuch"]) == 2


FULL_FM = {"name": "inbox", "description": "x", "when_to_use": "Use when x.", "disable-model-invocation": False, "model": "inherit", "effort": "low"}


def fm_messages(fm, name="inbox", **kw):
    return [m for _, m in audit.check_frontmatter(fm, name, **kw)]


def test_frontmatter_complete_is_clean():
    assert audit.check_frontmatter(dict(FULL_FM), "inbox") == []


def test_frontmatter_required_and_unknown_fields():
    msgs = fm_messages({"name": "inbox", "description": "x", "allowed_tools": "Read"})
    for key in ("when_to_use", "disable-model-invocation", "model", "effort"):
        assert any(f"required field {key}" in m for m in msgs)
    assert any("allowed_tools is not allowed" in m for m in msgs)


def test_frontmatter_stack_pack_skips_model_and_effort():
    fm = {"name": "stack-x", "description": "x", "when_to_use": "Load when x.", "disable-model-invocation": False}
    assert fm_messages(fm, "stack-x") == []
    assert any("overrides" in m for m in fm_messages({**fm, "effort": "high"}, "stack-x"))


def test_frontmatter_types_and_enums():
    msgs = fm_messages({**FULL_FM, "disable-model-invocation": "no", "model": "gpt-4", "effort": "huge",
                        "metadata": "1.0", "paths": 3, "compatibility": "x" * 501})
    for part in ("disable-model-invocation must be true or false", "model 'gpt-4'", "effort 'huge'",
                 "metadata must be a map", "paths must be", "compatibility has 501"):
        assert any(part in m for m in msgs), part


def test_frontmatter_fork_dependencies():
    msgs = fm_messages({**FULL_FM, "agent": "Explore", "background": False})
    assert any("agent works only with context: fork" in m for m in msgs)
    assert any("background works only with context: fork" in m for m in msgs)
    assert any("'nobody'" in m for m in fm_messages({**FULL_FM, "context": "fork", "agent": "nobody"}))
    assert fm_messages({**FULL_FM, "context": "fork", "agent": "planner"}, agents={"planner"}) == []


def test_frontmatter_preload_and_allowed_tools_path(tmp_path):
    fm = {**FULL_FM, "disable-model-invocation": True}
    assert any("blocks the preload" in m for m in fm_messages(fm, preloaded={"designer"}))
    tools = {**FULL_FM, "allowed-tools": ["Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/gone.py *)"]}
    assert any("scripts/gone.py" in m for m in fm_messages(tools, skill_dir=tmp_path))


def test_trigger_in_description_is_an_error(tmp_path):
    root = clone(tmp_path)
    skill = root / ".claude" / "skills" / "inbox" / "SKILL.md"
    text = skill.read_text()
    msgs = messages(audit.run(root, skill="inbox"), "skills")
    assert any("move it to when_to_use" in m for m in msgs)
    head, _, body = text.partition("\n---\n")
    head = "\n".join(line for line in head.splitlines() if not line.startswith("description:"))
    skill.write_text(head + "\ndescription: Show a human what waits on them, with links and age.\n"
                     "when_to_use: Use when a human asks for their inbox. Never use in scheduled runs.\n---\n" + body)
    msgs = messages(audit.run(root, skill="inbox"), "skills")
    assert not any("move it to when_to_use" in m or "names no trigger" in m for m in msgs)
