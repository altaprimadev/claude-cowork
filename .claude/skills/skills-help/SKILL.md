---
name: skills-help
description: List the claude-cowork skills with a one-line description each, grouped into human-invoked, pipeline stages, utilities, and stack packs, or show one skill in full. Use when a human asks which skills exist, what a skill does, or how to call it ("skill apa saja", "help", "cara pakai /inbox"), even if they do not say "skills-help".
argument-hint: "[skill name]"
metadata:
  version: "1.0.0"
  owner: claude-cowork
---
# Skills help

## Purpose

Show what claude-cowork can do, straight from the skill files. The list cannot go stale: a bundled script reads every `.claude/skills/<name>/SKILL.md` frontmatter and `CLAUDE.md` each time.

## When to use / not use

Use when:
- A human asks which skills exist, what one does, or how to call it.

Do not use when:
- The human wants to run a skill. Run that skill instead.
- A pipeline scheduled task runs. This skill only answers humans.

## Procedure

1. Run the script from the claude-cowork clone:
   ```bash
   python3 <skill-dir>/scripts/list_skills.py            # all skills, grouped
   python3 <skill-dir>/scripts/list_skills.py <name>     # one skill in full
   ```
   Groups come from `CLAUDE.md`:
   - **human**: the "Human-invoked skills" list. The human calls these.
   - **pipeline**: the stage map. The scheduled tasks run these.
   - **utility**: any other skill, for example `usage-status`.
   - **pack**: `stack-*` skills, loaded per repo profile.
2. Reply with the script output in a code block. Do not rewrite or reorder it.
3. Add at most two lines in semi-casual Bahasa Indonesia:
   - All skills: point to the human-invoked group as the place to start. Mention `/skills-help <name>` for detail.
   - One skill: say whether the human calls it or the pipeline runs it.

## Outputs

- One chat reply. No file or GitHub writes.

## Stop conditions

- After the reply.
- The script prints `error: no skill named ...`: show the known names it lists and stop.

## Anti-rationalization

| Thought | Reality |
|---|---|
| "I know the skills; I'll list them from memory." | Memory goes stale. Run the script. |
| "I'll translate every description into Indonesian." | Keep the script output as is. Add at most two lines. |
| "The human asked about a pipeline skill; I'll run it for them." | Pipeline stages run from the scheduled tasks. Explain, do not run. |

Original to claude-cowork. No upstream source.
