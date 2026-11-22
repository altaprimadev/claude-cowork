#!/usr/bin/env python3
"""PreCompact hook: print the compaction instructions for every claude-cowork session.

Claude Code adds a PreCompact hook's stdout to the instructions for the compaction
summary (code.claude.com/docs/en/hooks). The hook never blocks: it always exits 0.
Pipeline state lives in GitHub, so the summary keeps pointers, not copies.
"""

import sys

INSTRUCTIONS = """\
Compaction instructions (claude-cowork):
- On conflicting statements, keep only the latest.
- Reduce rejected or abandoned ideas to "Rejected: X (reason)".
- Keep clarifications as their resolved meaning only.
- Omit off-topic exchanges and superseded code versions.
- Tag anything not yet agreed on as [UNCERTAIN].
- Keep exactly: the human's standing instructions, open issue and PR numbers with their repo, the labels and comments posted in this run, pending scheduled checks, and any step that is half done.
- Keep facts with their source (command, file:line, or URL). Never turn an assumption into a fact.
- Drop raw tool output once its result is recorded. GitHub holds the pipeline state; re-read it instead of trusting the summary.
"""


def main() -> int:
    sys.stdin.read()  # Hook input JSON; not needed.
    sys.stdout.write(INSTRUCTIONS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
