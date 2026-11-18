# Labels, states, and gates

GitHub is the state store. Labels show where each issue or PR is in the pipeline.
`scripts/setup-labels.sh` creates every label below. Humans run it.

## Labels

| Label | Meaning | Set by |
|---|---|---|
| `ai:brief` | New brief from a human | Brief form (`.github/ISSUE_TEMPLATE/ai-brief.yml`) |
| `ai:triaged` | Brief classified | `intake-triager` |
| `size:small` | Small task: no design | `intake-triager` |
| `size:large` | Large task: design first (Gate 1) | `intake-triager` |
| `ai:needs-design` | Waiting for a design document | `intake-triager` |
| `ai:ready` | Ready to implement; dependencies done | `intake-triager` (small), `planner` (large) |
| `ai:in-progress` | A session works on it | Orchestrator, when it starts `implementer` |
| `ai:review-passed` | Agent review passed; waiting for human approval (Gate 2) | Orchestrator, after `review-two-stage` |
| `ai:changes-needed` | Agent review found blocking findings | Orchestrator, after `review-two-stage` |
| `ai:needs-human` | A human must decide; the session stopped | Any agent |
| `ai:blocked` | Blocked by a dependency or a repeated error | Any agent |
| `ai:report` | Daily report issue | `reporter` |

Rules:

- An issue has at most one of `ai:ready`, `ai:in-progress`, `ai:blocked`, `ai:needs-human` at a time.
- Every label change comes with a comment that says why.
- A human clears `ai:needs-human` by answering in a comment and removing the label. The next scheduled run picks the issue up again.
- Only humans approve and merge. Labels never replace an approval.

## State machine

```mermaid
stateDiagram-v2
    [*] --> Brief: human files the ai-brief form
    Brief --> Triaged: intake-triager (ai:triaged)
    Triaged --> Trivial: trivial change
    Triaged --> Small: size:small
    Triaged --> NeedsDesign: size:large + ai:needs-design
    Triaged --> NeedsHuman: unclear brief or autonomy too low

    NeedsDesign --> DesignPR: designer opens design PR
    DesignPR --> Planned: GATE 1 - human merges design PR
    DesignPR --> NeedsDesign: human requests changes
    Planned --> Waiting: planner creates sub-issues with open deps
    Planned --> Ready: planner sets ai:ready when deps are done
    Waiting --> Ready: deps closed

    Small --> Ready
    Trivial --> InProgress
    Ready --> InProgress: implementer (ai:in-progress)
    InProgress --> PROpen: PR with evidence
    InProgress --> Blocked: max_fix_attempts reached (ai:blocked)

    PROpen --> Stage1: spec-reviewer
    Stage1 --> ChangesNeeded: fail
    Stage1 --> Stage2: pass
    Stage2 --> ChangesNeeded: critical finding (ai:changes-needed)
    Stage2 --> ReviewPassed: ai:review-passed
    ChangesNeeded --> InProgress: implementer fixes
    ChangesNeeded --> NeedsHuman: max rounds reached

    ReviewPassed --> Merged: GATE 2 - human approves and merges
    Merged --> Production: GATE 3 - human promotes (Coolify or production branch)
    Production --> [*]

    NeedsHuman --> Triaged: human answers
    Blocked --> Ready: human or dependency unblocks
```

## Gates

| Gate | What | Who | Enforced by |
|---|---|---|---|
| Gate 1 | Design accepted | Human merges the design PR | Branch protection: PR, approval, CODEOWNERS |
| Gate 2 | Code accepted | Human approves the code PR | Branch protection: approval, required checks, dismiss stale reviews |
| Gate 3 | Production release | Human promotes in Coolify or merges to the protected production branch | Coolify permissions, branch protection on `production` |

Agents never pass a gate. As a second layer, `.claude/hooks/guard_bash.py` blocks merge and approve commands and pushes to `main`, `master`, and `production`.
