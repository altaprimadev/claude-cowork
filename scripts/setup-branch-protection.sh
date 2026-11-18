#!/usr/bin/env bash
# Configure branch protection on one branch of one repo.
#
# Default is --dry-run: print the request, change nothing.
# Pass --apply to change settings.
#
# Usage:
#   scripts/setup-branch-protection.sh owner/repo [--branch main] \
#       [--check "test"] [--check "lint"] [--approvals 1] [--apply]
#
# Enables: required PR, >= N approvals (default 1), dismiss stale reviews,
# code owner reviews, required status checks (strict), enforce for admins,
# no force pushes, no deletions.
# Needs: gh CLI, authenticated as a HUMAN repo admin. The agent never runs it.
# Idempotent: PUT replaces the protection with the same settings each run.

set -euo pipefail

REPO=""
BRANCH="main"
APPROVALS=1
APPLY=0
CHECKS=()

usage() { sed -n '2,16p' "$0" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="$2"; shift 2 ;;
    --check) CHECKS+=("$2"); shift 2 ;;
    --approvals) APPROVALS="$2"; shift 2 ;;
    --apply) APPLY=1; shift ;;
    --dry-run) APPLY=0; shift ;;
    -h|--help) usage ;;
    -*) echo "Unknown option: $1" >&2; usage ;;
    *) [[ -z "$REPO" ]] && REPO="$1" || usage; shift ;;
  esac
done

[[ -n "$REPO" ]] || usage
[[ "$APPROVALS" =~ ^[0-9]+$ ]] || { echo "--approvals must be a number" >&2; exit 1; }

contexts_json="[]"
if [[ ${#CHECKS[@]} -gt 0 ]]; then
  contexts_json=$(printf '%s\n' "${CHECKS[@]}" | python3 -c 'import json,sys; print(json.dumps([l.rstrip("\n") for l in sys.stdin if l.strip()]))')
fi

payload=$(cat <<JSON
{
  "required_status_checks": {"strict": true, "contexts": ${contexts_json}},
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": ${APPROVALS}
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON
)

endpoint="repos/${REPO}/branches/${BRANCH}/protection"

echo "Repo:     ${REPO}"
echo "Branch:   ${BRANCH}"
echo "Endpoint: PUT ${endpoint}"
echo "Current protection:"
if current=$(gh api "${endpoint}" 2>/dev/null); then
  echo "${current}" | python3 -m json.tool
else
  echo "  (none, or no permission to read)"
fi
echo "New protection:"
echo "${payload}" | python3 -m json.tool

if [[ ${#CHECKS[@]} -eq 0 ]]; then
  echo "WARNING: no --check given. No status check will be required." >&2
fi

if [[ "$APPLY" -ne 1 ]]; then
  echo "Dry run. Nothing changed. Re-run with --apply to apply."
  exit 0
fi

echo "${payload}" | gh api --method PUT "${endpoint}" --input - >/dev/null
echo "Applied."
