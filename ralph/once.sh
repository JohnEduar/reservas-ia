#!/usr/bin/env bash
# ralph/once.sh — Autonomous issue implementation script
#
# Usage:
#   ./ralph/once.sh <issue_number>
#
# Requires:
#   - claude CLI (claude --version)
#   - curl + jq
#   - GITHUB_TOKEN env var (read-only scope is enough)
#   - GITHUB_REPO  env var  (default: JohnEduar/reservas-ia)
#
# What it does:
#   1. Fetches the issue body + comments from GitHub REST API
#   2. Reads context from handoffs.md and architecture-checkpoint.md
#   3. Launches `claude` in non-interactive mode with a structured prompt
#   4. Claude implements the issue end-to-end (models → schemas → repos →
#      services → endpoints → migration → tests → handoff update)
#
# Exit codes:
#   0 — claude finished without error
#   1 — missing dependency or argument
#   2 — GitHub API error

set -euo pipefail

# ── Validation ────────────────────────────────────────────────────────────────

ISSUE_NUMBER="${1:-}"
if [[ -z "$ISSUE_NUMBER" ]]; then
  echo "Usage: $0 <issue_number>" >&2
  exit 1
fi

for dep in claude curl jq; do
  if ! command -v "$dep" &>/dev/null; then
    echo "ERROR: '$dep' is not installed or not in PATH." >&2
    exit 1
  fi
done

GITHUB_REPO="${GITHUB_REPO:-JohnEduar/reservas-ia}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

# ── Fetch issue from GitHub ───────────────────────────────────────────────────

AUTH_HEADER=""
if [[ -n "$GITHUB_TOKEN" ]]; then
  AUTH_HEADER="Authorization: Bearer $GITHUB_TOKEN"
fi

echo "→ Fetching issue #$ISSUE_NUMBER from $GITHUB_REPO..."

ISSUE_JSON=$(curl -sf \
  ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
  "https://api.github.com/repos/$GITHUB_REPO/issues/$ISSUE_NUMBER") || {
  echo "ERROR: Could not fetch issue #$ISSUE_NUMBER. Check GITHUB_TOKEN and repo name." >&2
  exit 2
}

ISSUE_TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
ISSUE_BODY=$(echo "$ISSUE_JSON"  | jq -r '.body // "(no body)"')
ISSUE_LABELS=$(echo "$ISSUE_JSON" | jq -r '[.labels[].name] | join(", ")')

echo "   Title:  $ISSUE_TITLE"
echo "   Labels: $ISSUE_LABELS"

# Fetch first page of comments (usually enough for context)
COMMENTS_JSON=$(curl -sf \
  ${AUTH_HEADER:+-H "$AUTH_HEADER"} \
  "https://api.github.com/repos/$GITHUB_REPO/issues/$ISSUE_NUMBER/comments?per_page=20") || COMMENTS_JSON="[]"

COMMENTS=$(echo "$COMMENTS_JSON" | jq -r '.[] | "[@\(.user.login)] \(.body)"' | head -20)

# ── Read project context ──────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

HANDOFFS=""
if [[ -f "$PROJECT_ROOT/handoffs.md" ]]; then
  HANDOFFS=$(tail -100 "$PROJECT_ROOT/handoffs.md")
fi

ARCH_CHECKPOINT=""
if [[ -f "$PROJECT_ROOT/architecture-checkpoint.md" ]]; then
  ARCH_CHECKPOINT=$(head -80 "$PROJECT_ROOT/architecture-checkpoint.md")
fi

# ── Build prompt (temp file avoids heredoc shell-expansion issues) ────────────
# printf '%s' never interprets content, so backticks/$(…) in GitHub data are safe.

PROMPT_FILE=$(mktemp)
trap 'rm -f "$PROMPT_FILE"' EXIT

# Part 1 – static header
cat >> "$PROMPT_FILE" <<'STATIC'
You are implementing GitHub Issue #STATIC
printf '%s' "$ISSUE_NUMBER" >> "$PROMPT_FILE"
cat >> "$PROMPT_FILE" <<'STATIC'
 for the GlampBook glamping reservation platform.

## Issue to implement

STATIC

# Part 2 – dynamic issue data
printf '**Title:** %s\n' "$ISSUE_TITLE"      >> "$PROMPT_FILE"
printf '**Labels:** %s\n\n' "$ISSUE_LABELS"  >> "$PROMPT_FILE"
printf '**Description:**\n%s\n\n' "$ISSUE_BODY" >> "$PROMPT_FILE"
printf '**Comments:**\n%s\n\n---\n\n' "$COMMENTS" >> "$PROMPT_FILE"

# Part 3 – static stack + locations
cat >> "$PROMPT_FILE" <<'STATIC'
## Project context

### Stack
- FastAPI + SQLAlchemy + MySQL (production) / SQLite in-memory (tests)
- Layered architecture: models → schemas → repositories → services → endpoints
- Repository pattern with BaseRepository[T] generic
- Soft delete via is_active (never hard-delete rows)
- JWT auth via python-jose
- Domain exceptions: services raise typed exceptions, global handler maps to HTTP codes
- Tests: pytest + SQLite in-memory (StaticPool), dependency_overrides[get_db]

### Key file locations
- Models:       backend/app/models/
- Schemas:      backend/app/schemas/
- Repositories: backend/app/repositories/
- Services:     backend/app/services/
- Endpoints:    backend/app/api/v1/endpoints/
- Exception map:backend/app/core/exception_handlers.py
- Router mount: backend/app/api/v1/router.py
- Tests:        backend/tests/
- Migrations:   backend/migrations/versions/

### Global exception handler pattern (ALWAYS use this — no try/except in endpoints)
Services raise typed exceptions (e.g. UserNotFoundError).
Add them to _EXCEPTION_STATUS_MAP in backend/app/core/exception_handlers.py.
Endpoints stay clean — zero try/except blocks.

STATIC

# Part 4 – dynamic project context
printf '### Recent handoff summary (last 100 lines of handoffs.md)\n%s\n\n' \
  "$HANDOFFS" >> "$PROMPT_FILE"
printf '### Architecture checkpoint highlights\n%s\n\n---\n\n' \
  "$ARCH_CHECKPOINT" >> "$PROMPT_FILE"

# Part 5 – static task steps
cat >> "$PROMPT_FILE" <<'STATIC'
## Your task

Implement Issue #STATIC
printf '%s' "$ISSUE_NUMBER" >> "$PROMPT_FILE"
cat >> "$PROMPT_FILE" <<'STATIC'
 end-to-end following these steps in order:

1. **Read** all existing relevant files before editing any of them.
2. **Models** — add SQLAlchemy models to backend/app/models/ if needed.
3. **Schemas** — add Pydantic v2 schemas (Create/Update/Response pattern).
4. **Repository** — add repository class extending BaseRepository.
5. **Service** — add service with typed exception classes. NO try/except in service — raise, do not catch.
6. **Endpoints** — add clean router. NO try/except. Register in backend/app/api/v1/router.py.
7. **Exception handler** — add new exception types to _EXCEPTION_STATUS_MAP.
8. **Migration** — create an Alembic migration with a descriptive filename. Set down_revision to the latest existing migration.
9. **Tests** — add backend/tests/test_<feature>.py with pytest. Cover: happy path, 401, 403, 404, 409, 422 where applicable.
10. **Handoff** — append a new entry to handoffs.md describing what was built.

Do NOT skip any step. Do NOT commit. Do NOT start the server.
STATIC

# ── Run claude ────────────────────────────────────────────────────────────────

echo ""
echo "→ Launching claude to implement issue #$ISSUE_NUMBER..."
echo "  (This may take several minutes)"
echo ""

cd "$PROJECT_ROOT"

# $(cat file) captures bytes as-is — shell does NOT re-interpret backticks or $() in the string
claude --dangerously-skip-permissions -p "$(cat "$PROMPT_FILE")"

echo ""
echo "✓ ralph/once.sh finished for issue #$ISSUE_NUMBER"
