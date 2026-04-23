---
name: issue-work
description: End-to-end GitHub/Forgejo ticket workflow. Use when the user shares a ticket URL (github.com/owner/repo/issues/N or /pull/N), a shorthand like owner/repo#123, asks to "start on ticket", "pick up this issue", "work on this ticket", or pastes issue text asking for implementation. Fetches ticket with all comments and linked work, creates a worktree, spawns parallel exploration agents, proposes an implementation plan for approval, implements, runs tests, then runs parallel self-review (correctness/security/simplicity) before returning for human review.
---

# Issue Work

End-to-end workflow for taking a GitHub or Forgejo ticket from URL to review-ready implementation. Four phases: **Intake → Plan → Implement → Self-Review**, with a human approval checkpoint between Plan and Implement.

Standalone — does not require any specific note system. Ships in the Athena Notes plugin, but writes state under `~/.claude/issue-work/` (not the notes vault).

---

## Inputs Accepted

- GitHub issue URL: `https://github.com/{owner}/{repo}/issues/{N}`
- GitHub PR URL: `https://github.com/{owner}/{repo}/pull/{N}`
- Forgejo URL: `https://{host}/{owner}/{repo}/(issues|pulls)/{N}`
- Shorthand: `{owner}/{repo}#{N}` (GitHub)
- Raw pasted ticket text (asks for repo)

## State Root

All per-ticket state lives at:

```
~/.claude/issue-work/{owner}-{repo}-{N}/
```

This survives worktree teardown. Resume is supported by reading `progress.md` frontmatter `status:` field.

---

## Phase 0 — Resume Check

Before anything else, compute the state-dir path from the input. If `~/.claude/issue-work/{owner}-{repo}-{N}/progress.md` exists:

1. Read its frontmatter `status:` field.
2. Report to the user: "Found existing work on {ticket}. Status: {status}. Resume or refresh?"
3. On **resume**, skip to the phase after the last completed status.
4. On **refresh**, continue with the full flow (will overwrite prior files).

Do not re-fetch or re-plan unless the user says refresh.

---

## Phase 1 — Intake

### 1.1 Detect source

Match the input against these patterns **in order** (stop at the first match):

```bash
# 1. GitHub URL — check this FIRST (note the /issues/ path overlaps with Forgejo)
^https?://github\.com/([^/]+)/([^/]+)/(issues|pull)/([0-9]+)

# 2. Shorthand — always GitHub
^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)#([0-9]+)$

# 3. Forgejo URL — only reached if neither of the above matched
^https?://([^/]+)/([^/]+)/([^/]+)/(issues|pulls)/([0-9]+)
```

**Ordering matters.** GitHub issue URLs also satisfy the Forgejo pattern (both use `/issues/`), so GitHub must be checked first. Only PRs differ by path (`/pull/` vs `/pulls/`).

If none match and the input is ticket-like prose, treat as pasted text and **ask which repo** before proceeding.

### 1.2 Create state directory

```bash
mkdir -p "$HOME/.claude/issue-work/{owner}-{repo}-{N}"
```

### 1.3 Spawn `ticket-analyst` sub-agent

Invoke the `ticket-analyst` agent with the ticket reference and the state-dir path. It writes `context.md` with ticket body, comments, linked refs, inferred open questions.

Do **not** inline the fetch logic here — the agent owns that. Read `context.md` after it returns.

### 1.4 Resolve local clone

See [references/repo-resolution.md](references/repo-resolution.md) for details. Short version:

```bash
# Look for a clone matching owner/repo under ~/code/ (1 and 2 levels deep)
Glob(pattern="$HOME/code/*/.git")
Glob(pattern="$HOME/code/*/*/.git")
# For each match, check remote URL matches owner/repo
```

If no local clone: ask before running `gh repo clone {owner}/{repo} ~/code/{repo}`.

### 1.5 Pre-flight checks

Run all of these against the trunk (not a worktree).

**First, detect the default branch** (don't assume `main`):

```bash
DEFAULT_BRANCH=$(gh repo view {owner}/{repo} --json defaultBranchRef --jq .defaultBranchRef.name)
# Forgejo equivalent — use the API from references/fetch-ticket.md
```

**Then run the rest of the pre-flight:**

```bash
gh auth status                                            # GitHub auth
[[ -n "${FORGEJO_TOKEN:-$GITEA_TOKEN}" ]]                 # Forgejo auth (only if forgejo ticket)
git -C "$TRUNK" fetch origin "$DEFAULT_BRANCH"            # fetch the actual default branch

# Working tree clean? (modified or staged — ignore untracked)
git -C "$TRUNK" status --porcelain | grep -E '^[ MADRC]'
```

If the trunk is dirty (modified/staged, not just untracked), stop and offer: stash / commit / abort. Do not silently stash.

### 1.6 Create worktree

Use the `EnterWorktree` tool with:

- **Name**: `{repo}.{N}-{kebab-slug}` (max 60 chars)
  - `kebab-slug` = ticket title, lowercased, non-alphanumerics → `-`, collapsed, trimmed
- **Base branch**: the default branch from 1.5
- **Branch name**: `issue-{N}-{kebab-slug}` (or match repo convention if apparent from recent branches)

After worktree creation, `cd` to the worktree.

### 1.7 Write initial progress.md

```markdown
---
status: intake
ticket: {url-or-shorthand}
worktree: {abs-path}
branch: {branch-name}
base: {default-branch}
started: {iso8601}
---

## Intake complete

- Context file: ~/.claude/issue-work/{owner}-{repo}-{N}/context.md
- Worktree: {abs-path}
- Base branch: {default-branch}
```

---

## Phase 2 — Plan

### 2.1 Spawn parallel exploration

**Always** spawn one `Explore` agent. **Conditionally** spawn a second `Explore` if the ticket clearly spans two distinct areas (e.g., frontend + backend, API + client SDK).

Send a **single message with multiple Task tool calls** — do not spawn sequentially.

Prompt template for each Explore agent:

> Map the codebase area relevant to ticket #{N}: "{title}".
>
> **Scope** (one of): {primary area | secondary area}
>
> Starting points (from ticket body/comments): {files, functions, modules mentioned}
>
> Produce a concise map:
> - Affected modules and files (with paths)
> - Existing patterns/abstractions worth reusing
> - Test locations and conventions in this area
> - Any gotchas or non-obvious coupling
>
> Write your findings to `~/.claude/issue-work/{owner}-{repo}-{N}/explore.md` (append if a second Explore is running — use a `## Area: {name}` heading).

### 2.2 External research (conditional, inline)

If the ticket references libraries or APIs **not** present in the repo's manifests, do research inline.

First, discover which manifests exist in the repo:

```bash
# List manifests that actually exist at the repo root
for f in package.json go.mod Cargo.toml requirements.txt pyproject.toml Gemfile pom.xml build.gradle; do
  [[ -e "$f" ]] && echo "$f"
done
```

Then for each manifest found, grep its declared dependencies and compare against library names mentioned in the ticket. A library named in the ticket but absent from every manifest is a candidate for external research.

Use `WebSearch` + `WebFetch` to look up official docs. Capture findings directly in `plan.md` under a **Research** section. Do not create a separate agent or file.

### 2.3 Synthesize plan.md

After exploration returns, write `plan.md`:

```markdown
---
status: planned
ticket: {url}
updated: {iso8601}
---

## Problem

{2–3 sentences from context.md + explore.md}

## Approach

{high-level strategy}

## Affected Files

- `path/to/file.ts` — {what changes}
- `path/to/other.ts` — {what changes}

## Test Strategy

{what tests to add, what suites to run, any new fixtures}

## Research

{external docs/references, only if relevant}

## Open Questions

- {items to flag for the user before implementation}

## Non-goals

- {explicit scope boundaries}
```

### 2.4 Approval checkpoint

This is a hard stop. **Do not proceed to Phase 3 without explicit user approval.**

Present the full `plan.md` contents inline to the user with a clear prompt:

> **Plan ready for review** — `~/.claude/issue-work/{owner}-{repo}-{N}/plan.md`
>
> {paste plan.md contents}
>
> Reply `approve` to begin implementation, or describe changes you'd like.

Then wait for the user's next message. Do not implement anything until you see an approval.

On amendment: overwrite `plan.md` with the revised version, keep `status: planned` in frontmatter, and re-present. Iterate until approved.

(If the harness happens to be in Plan Mode when this skill runs, `ExitPlanMode` is the harness-native approval gate and you can use it in place of the inline prompt above. Do not try to enter Plan Mode from inside the skill — that's not a thing.)

---

## Phase 3 — Implement

After user approval:

### 3.1 Update status

```bash
# Set progress.md frontmatter status: implementing
```

### 3.2 Re-read plan.md

`plan.md` is the source of truth. If anything in the conversation contradicts it, defer to the plan — or stop and ask before diverging.

### 3.3 Commits

- Atomic: one logical unit per commit
- Message style: match `git log --oneline -20` conventions in **this repo** (not global defaults)
- **Never** add `Co-authored-by: Claude` or any AI signature trailer
- **Never** use `--no-verify` to skip hooks

### 3.4 Test suite detection

Run tests after implementation. Detect by manifest:

| Manifest | Command |
|---|---|
| `package.json` with `test` script | `npm test` or `yarn test` or `pnpm test` (match lockfile) |
| `pyproject.toml` | `pytest` |
| `Cargo.toml` | `cargo test` |
| `go.mod` | `go test ./...` |
| `nx.json` / `turbo.json` | `nx affected -t test` or `turbo test` |

Also run lint + typecheck when configured:

- TypeScript: `tsc --noEmit` or repo script
- Python: `ruff check` / `mypy`
- Go: `go vet ./...`
- Rust: `cargo clippy`

### 3.5 On failure

Loop: diagnose → fix → commit → rerun. **Hard cap at 3 attempts.** On the 4th failure, stop and report the failing output to the user.

### 3.6 Progress log

After each test run, append to `progress.md`:

```markdown
## {iso8601} — commit {sha7}

{one-line commit subject}

Tests: {pass/fail summary}
Lint/typecheck: {summary}
```

When implementation is complete and green, keep `status: implementing` until Phase 4 finishes.

---

## Phase 4 — Self-Review

### 4.1 Spawn 3 parallel `impl-reviewer` agents

Send a **single message with 3 Task tool calls**. Each gets:

- `lens`: `correctness` | `security` | `simplicity`
- `diff_range`: `{base}...HEAD`
- `worktree_path`: absolute
- `plan_path`: `~/.claude/issue-work/{owner}-{repo}-{N}/plan.md`
- `output_path`: `~/.claude/issue-work/{owner}-{repo}-{N}/review-{lens}.md`

### 4.2 Synthesize summary.md

After all three return, read their files and write:

```markdown
---
status: reviewed
ticket: {url}
reviewed: {iso8601}
---

## Headline

{one sentence: clean or N critical / M major issues surfaced}

## Critical Issues

- [{lens}] [{file}:{line}] {issue}

## Major Issues

- [{lens}] [{file}:{line}] {issue}

## Minor / Nit

- {bulleted, grouped by lens}

## Ship Readiness

{Clear recommendation: "Ship as draft" | "Fix criticals first" | "Re-plan"}
```

Set `progress.md` `status: reviewed`.

### 4.3 Present to user

Show the user:

1. The headline + Critical + Major findings inline
2. Path to `summary.md` + individual `review-{lens}.md` files
3. The suggested next step:

```bash
cd {worktree}
gh pr create --draft --title "{ticket-title}" \
  --body-file ~/.claude/issue-work/{owner}-{repo}-{N}/summary.md
```

(Or for Forgejo, the equivalent `tea pulls create` or API call.)

**Do not auto-open the PR.** User approves ship.

---

## Edge Cases

| Case | Behavior |
|---|---|
| Worktree already exists for this ticket | Skip creation; `EnterWorktree` into it; resume from `progress.md` status |
| Trunk dirty (modified/staged) | Stop. List files. Offer stash / commit / abort |
| Ticket is a PR (review work, not new work) | Skip worktree creation; `gh pr checkout {N}` in trunk or fetch branch; swap Phase 3 for "review against plan"; Phase 4 reviewers still run |
| Tests fail 3× | Stop; surface last failure output; ask user |
| Critical review findings | Present prominently; recommend fix-before-ship; never auto-ship |
| User amends plan after approval | Overwrite `plan.md`; reset status `planned`; re-enter ExitPlanMode |
| Repo not cloned locally | Ask before `gh repo clone` to `~/code/{repo}` |
| Forgejo ticket | `ticket-analyst` uses REST API; everything else identical |
| Pasted raw text (no URL) | Skip fetch; ask user for repo; `context.md` has only Body |
| User says "refresh" on a resumed ticket | Overwrite prior state files; restart from Phase 1 |

---

## Things This Skill Does NOT Do

- Open PRs automatically (the user runs `gh pr create` when ready)
- Push branches automatically
- Modify files outside the worktree and the state dir
- Add AI signatures to commits or PRs
- Skip hooks (`--no-verify`) or bypass signing
- Write notes into `.notes/` or any note system — state goes to `~/.claude/issue-work/` only

---

## References

Detailed recipes that load on demand:

- [references/fetch-ticket.md](references/fetch-ticket.md) — exact gh/tea CLI commands, pagination, rate limits, Forgejo API auth
- [references/repo-resolution.md](references/repo-resolution.md) — local clone discovery, remote URL matching, clone-if-missing prompt

## Related Agents

- `ticket-analyst` — Phase 1 fetch + digest (model: haiku)
- `impl-reviewer` — Phase 4 parallel reviewer with `lens` argument; carries its own lens prompts inline (model: sonnet)
