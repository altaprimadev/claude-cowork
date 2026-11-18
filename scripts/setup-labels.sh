#!/usr/bin/env bash
# Create or update the pipeline labels in one or more repos.
# Idempotent: `gh label create --force` updates existing labels.
#
# Usage: scripts/setup-labels.sh owner/repo [owner/repo ...]
# Needs: gh CLI, authenticated as a HUMAN with admin or maintain rights.
# The agent never runs this script.

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 owner/repo [owner/repo ...]" >&2
  exit 1
fi

# name|color|description
LABELS=(
  "ai:brief|1d76db|New brief from a human"
  "ai:triaged|0e8a16|Classified by intake"
  "size:small|c2e0c6|Small task: no design needed"
  "size:large|f9d0c4|Large task: design (Gate 1) first"
  "ai:needs-design|fbca04|Waiting for a design document"
  "ai:ready|0e8a16|Ready to implement; dependencies done"
  "ai:in-progress|5319e7|A session is working on it"
  "ai:review-passed|0e8a16|Agent review passed; awaiting human approval (Gate 2)"
  "ai:changes-needed|d93f0b|Agent review found blocking issues"
  "ai:needs-human|b60205|Needs a human decision; the session stopped"
  "ai:blocked|000000|Blocked by a dependency or an error"
  "ai:report|bfdadc|Daily report issue"
)

for repo in "$@"; do
  echo "==> $repo"
  for entry in "${LABELS[@]}"; do
    IFS='|' read -r name color desc <<<"$entry"
    gh label create "$name" --repo "$repo" --color "$color" --description "$desc" --force
    echo "    ok  $name"
  done
done
