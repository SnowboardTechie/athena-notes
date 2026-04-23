---
name: pr-self-review
description: Iterative self-review loop for PRs you authored. Runs the three-lens parallel review (correctness / security / simplicity), pre-feeds reviewers with related open issues and project-note context so they can defer overlaps, and walks findings through a four-action triage (accept / push-back / issue / skip) that commits accepted edits and loops until the diff is clean. Triggers on `/pr-self-review [pr-url]`, "review my PR", or invocation from `issue-work` Phase 4.
---

# PR Self-Review

Wraps the manual review → fix → commit → re-review loop for PRs **you authored**. Carries session state so reviewers don't re-raise findings you've already pushed back on, and surfaces related open issues + `.notes/` decisions so a reviewer's nit that duplicates a known ticket or a settled exploration can be deferred with one keystroke.

Not for reviewing other people's work.

Three entry points:

- `/pr-self-review <pr-url>` — fresh session, points at any open PR you authored.
- `/pr-self-review` — no URL; infers the PR from the current branch via `gh pr view`.
- Invoked from `issue-work` Phase 4 — worktree + branch already exist, no PR yet.

---

## State Root

**Standalone modes** (`pr-url`, `branch-inference`):

```
~/.claude/pr-self-review/{owner}-{repo}-{pr-N-or-branch-slug}/
```

**Invoked from `issue-work` Phase 4** (`pre-pr` mode): reuse the caller's state dir —

```
~/.claude/issue-work/{owner}-{repo}-{N}/
```

so `review-{lens}.md` / `summary.md` land at the path `issue-work` Phase 4.3 already reads. Do not create a second parallel dir for pre-pr runs.

Session state (push-back rationales, skip list, suppressed-finding keys, filed-issue URLs) is **in-memory only** — never persisted across skill runs. Cache files (related-issues, related-notes) overwrite on each run.

---

## Phase 0 — Entry resolution

Detect the mode from arguments and context:

### 0.1 `pre-pr` (invoked from issue-work)

The skill recognizes it's being delegated to when the invoker passes a `state_dir:` argument pointing under `~/.claude/issue-work/`. In this case:

- Worktree path and branch are already set up.
- The caller's `plan.md` exists in the state dir — use it as ground truth for reviewers.
- There is no PR yet. Skip the PR-lookup step; skip all `linked-to-PR` issue fetches (degrade to path-touching + label-matched only).
- Skip the commit-and-push loop's push step for the first pass if the branch is still unpushed — just commit. Let `issue-work` Phase 4.3 drive the eventual push + PR creation via `/ship`.

### 0.2 `pr-url`

Argument matches `^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)` or the Forgejo equivalent (`/pulls/` path). Parse `owner`, `repo`, `N`.

- Resolve local clone (reuse pattern from `skills/issue-work/references/repo-resolution.md`). Ask before cloning if missing.
- Fetch PR details: `gh pr view {N} --repo {owner}/{repo} --json number,title,headRefName,baseRefName,body,url,author`.
- Confirm the PR author matches the current `gh auth status` user. If not, stop: "This skill is for PRs you authored. {author} authored this PR — use `/code-review` instead."
- Create or enter worktree at `.claude/worktrees/{repo}.pr-{N}-{kebab-slug}` (follow `issue-work` Phase 1.6 convention, but with `pr-{N}` instead of `{N}`). Checkout the PR branch there: `git fetch origin pull/{N}/head:{headRefName} && git checkout {headRefName}`.

### 0.3 `branch-inference`

No argument. From the current working directory:

```bash
branch=$(git branch --show-current)
gh pr view --json number,url,headRefName,baseRefName,author
```

If no open PR for the current branch, stop: "No open PR on `{branch}`. Push the branch and open a PR first (try `/ship`), or pass a PR URL."

Otherwise treat as `pr-url` mode from here on — same author check, same worktree handling (if already in a worktree for this branch, reuse it; don't nest).

### 0.4 Pre-flight

Common to all three modes:

- `gh auth status` must pass for GitHub PRs; Forgejo needs `FORGEJO_TOKEN` (or `GITEA_TOKEN`) in env, same as `issue-work` Phase 1.5.
- Working tree must be clean (no modified/staged files; untracked OK). Dirty → **refuse**: "Working tree has uncommitted changes. Commit, stash, or discard before starting a review loop." Do not silently stash.
- Record mode, owner, repo, PR number (or branch for `pre-pr`), worktree path, and state-dir path in memory for the rest of the run.

---

## Phase 1 — Pre-review context fetch (once per skill run)

Two parallel caches. Populate both in a single message where possible.

### 1.1 Related-issues cache

Three dimensions; union the results; deduplicate by issue number.

**A. Linked to the PR** (skip in `pre-pr` mode — no PR yet):

Parse the PR body + timeline for `Closes #N`, `Fixes #N`, `Refs #N`, `Related #N` (case-insensitive). Also fetch cross-references:

```bash
gh api "repos/{owner}/{repo}/issues/{pr-number}/timeline" --paginate \
  --jq '[.[] | select(.event=="cross-referenced") | .source.issue.number] | unique'
```

**B. Path-touching** (all modes):

Compute the list of changed files:

```bash
git diff --name-only {base}...HEAD
```

Extract basenames (no extension) and top-level directories. Grep open issues for any of those tokens:

```bash
for term in "${basenames[@]}" "${top_level_dirs[@]}"; do
  gh issue list --repo {owner}/{repo} --state open --search "$term in:title,body" \
    --json number,title,url,labels,body --limit 10
done
```

Dedup by number after the union.

**C. Label-matched** (all modes):

```bash
for label in tech-debt known-issue follow-up; do
  gh issue list --repo {owner}/{repo} --state open --label "$label" \
    --json number,title,url,labels,body --limit 20
done
```

The label list is configurable: if the user's `~/.claude/athena/pr-self-review.md` exists with `related_labels: [...]`, use that list instead. Otherwise use the default above. Do not silently add labels beyond what's listed — it drowns reviewers in noise.

**Forgejo equivalents:** `tea api` against `/repos/{owner}/{repo}/issues?state=open&q={term}` for (B) and `?labels={id}` for (C). Resolve label names → integer IDs first (same pattern as `issue-create` Stage 2.2).

Write the merged cache to `{state-dir}/related-issues.json`:

```json
[
  {
    "number": 17,
    "title": "...",
    "url": "https://...",
    "labels": ["tech-debt"],
    "match_reason": "linked | path | label",
    "body_excerpt": "first 400 chars"
  }
]
```

### 1.2 Related-notes cache

First, check `.notes/` availability in the trunk (the worktree shares the symlink):

```bash
# Resolve trunk root — follows agent-workspace/SKILL.md
toplevel=$(git rev-parse --show-toplevel)
if [ -f "${toplevel}/.git" ]; then
  TRUNK_ROOT=$(dirname "$(git rev-parse --git-common-dir)")
else
  TRUNK_ROOT="$toplevel"
fi
```

Then: `Glob(pattern="{TRUNK_ROOT}/.notes")`. Empty → log once ("No project notes available; skipping archivist phase.") and write `{state-dir}/related-notes.json` as `[]`. Do not auto-create `.notes/` — this is a read-only review skill; the user opts into notes via `/athena-setup`.

If `.notes/` is present, extract keyword topics from the diff:

- Changed-file basenames (no extension), lowercased.
- Top-level directory names of changed files.
- New exported symbols — `git diff {base}...HEAD` + grep for added lines matching `^\+(export\s+|def |class |function |pub fn )` to pull function/class names. Keep the simplest extraction; do not try to parse ASTs.

Dedupe the topic list, cap at 6 topics (budget control). Then fire parallel archivist calls in **a single message with multiple Task tool calls** (matching the meeting-sync precedent — see [skills/meeting-sync/SKILL.md](../meeting-sync/SKILL.md)):

```
Task(
  subagent_type="archivist",
  description="Notes related to {topic}",
  prompt="scope: published

Find any published notes that touch {topic}. Focus on decisions, explorations, and idea/known-issue notes — the kind of context a reviewer would want to know about before re-proposing an alternative. Return matches with type, path, title, a 1-line summary, and one key excerpt per match."
)
```

Budget: up to 6 parallel calls. Synthesize results into `{state-dir}/related-notes.json`:

```json
[
  {
    "path": ".notes/decisions/api-versioning.md",
    "title": "API versioning strategy",
    "note_type": "decision",
    "summary": "Chose path-based over header-based versioning because ...",
    "topic_match": "api"
  }
]
```

If every archivist call returns "no matches," write `[]` — do not error.

---

## Phase 2 — Review pass

### 2.1 Spawn three parallel `impl-reviewer` agents

Single message, three Task calls. Each gets:

- `lens` — `correctness` | `security` | `simplicity`
- `diff_range` — `{base-branch}...HEAD`
- `worktree_path` — absolute
- `plan_path` — `{state-dir}/plan.md` if present (pre-pr mode), else `null`
- `output_path` — `{state-dir}/review-{lens}.md`
- `related_issues_path` — `{state-dir}/related-issues.json`
- `related_notes_path` — `{state-dir}/related-notes.json`

Reviewers carry their full lens prompt inline (see `agents/impl-reviewer.md`). The two `related_*` paths are the new inputs — the reviewer reads them and, for each finding, checks whether any cached issue or note overlaps. On overlap, the finding carries an optional `related_issue: #N` or `related_note: {path}` line.

Reviewers do **not** change behavior when the caches are empty — missing-file and empty-list are both treated as "no related context," and the output schema stays stable.

### 2.2 Filter

After the three reviewers return, merge their findings and filter against the in-memory **session suppression set** (initially empty):

- Suppression key: `{lens}|{file}|{line}|{sha8(message)}`. The message hash tolerates whitespace differences but catches rewording.
- Findings whose key is already suppressed are dropped before triage.

Cross-lens observations (the reviewer's optional bottom-of-file section) surface as normal findings under the lens that noticed them.

### 2.3 Triage

See [references/triage-ui.md](references/triage-ui.md) for the per-finding prompt shape and the batch fallback.

Short version: walk unsuppressed findings from Critical → Major → Minor → Nit. For each, present file:line, the finding text, any `related_issue` / `related_note` context, and ask for one of:

- **accept** — Claude makes the edit in the worktree. No commit yet; batched at end of pass.
- **push-back <reason>** — record reason in session state; add finding key to suppression set.
- **issue** — hand off to `/issue-create` for dedup + filing. Pre-fill the issue body with the finding text, the offending file:line, and a link back to the PR. Filed-issue URL goes into session state so the same finding isn't re-filed next pass.
- **skip** — drop silently for this session. Add key to suppression set.

**Default action when a finding carries a `related_*` tag:** suggest `skip` and show the related issue/note inline as the rationale. Override stays one keystroke away.

At the end of triage, the pass has accumulated a set of accepted edits.

### 2.4 Commit + push

If any edits were accepted this pass:

- Stage only the touched files (no `git add -A`).
- Commit with a message that names the lens(es) involved: `review: address {correctness,simplicity} findings` (or whichever lenses contributed). Never add AI-attribution trailers.
- Push to the PR branch: `git push origin HEAD` — **skip the push in `pre-pr` mode if the branch is still unpushed locally** (let `issue-work` Phase 4.3 / `/ship` drive the first push).
- Never use `--no-verify`.

If no edits were accepted (all push-back / issue / skip), skip the commit and push.

### 2.5 Loop check

- **All findings across the pass were push-back / issue / skip, with zero accepts** → the code didn't change; review-ing the same diff again would produce the same findings. Exit the loop.
- **Any accepts** → loop: update `diff_range` nothing (it's already `{base}...HEAD` and HEAD moved), go back to Phase 2.1. Cap at 5 passes to prevent runaway loops; on the 5th pass, stop and ask the user whether to continue.
- **User says "done" at any point** → exit loop immediately.

---

## Phase 3 — Summary + exit

### 3.1 Write summary.md

At `{state-dir}/summary.md`:

```markdown
---
status: reviewed
target: {pr-url-or-branch}
reviewed: {iso8601}
passes: {N}
---

## Headline

{one sentence: clean after N passes | N critical still open | etc.}

## Accepted this session

- [pass {k}] [{lens}] [{file}:{line}] {one-line summary of fix}

## Pushed back

- [{lens}] [{file}:{line}] {finding} — rationale: {user's reason}

## Filed as issues

- [{lens}] [{file}:{line}] {finding} → {issue-url}

## Skipped

- [{lens}] [{file}:{line}] {finding}

## Ship Readiness

{Clear recommendation: "Ready to merge" | "Outstanding criticals — do not merge" | "User opted to exit with open findings"}
```

This is the same shape `issue-work` Phase 4.3 reads for the PR description. Preserve it.

### 3.2 Mode-specific exit

- **`pr-url` / `branch-inference`:** Report summary inline + PR URL + "{N} passes; {M} findings accepted and pushed." No `/ship` invocation — the PR already exists; each pass's push already updated it.
- **`pre-pr` (from issue-work):** Return control to the caller. `issue-work` Phase 4.3 reads the summary and presents the ship gate as before. Do not invoke `/ship` from inside this skill in pre-pr mode — that's `issue-work`'s gate.

---

## Edge Cases

| Case | Behavior |
|---|---|
| PR author isn't the current user | Stop. Tell the user this skill is for PRs they authored; point at `/code-review`. |
| Dirty working tree on invocation | Refuse. Never silently stash. |
| No open PR for current branch (`branch-inference`) | Stop. Suggest `/ship` or a PR URL. |
| `.notes/` missing | Skip archivist phase silently; write `related-notes.json` as `[]`; proceed. |
| `gh` not authenticated | Stop. Surface the auth error. |
| Archivist returns nothing for every topic | `related-notes.json = []`; proceed. |
| A pass's fix introduces a regression | Next pass flags it as a normal finding. Suppression only filters **explicit push-backs** and **skips**, not accepts. |
| User says "done" mid-triage | Finish any accepted edits from this pass, commit + push, write summary, exit. |
| 5 passes reached | Ask the user whether to continue for another 5 or exit. |
| Worktree already exists for this PR | Reuse it; don't nest. |
| Forgejo PR | `gh` replaced with Forgejo API (pattern from `skills/ship/SKILL.md` and `skills/issue-create/SKILL.md` Stage 4.2). Everything else is identical. |
| Invoked from issue-work but `plan.md` missing | Proceed with `plan_path: null`; reviewers fall back to "no plan ground truth" (they already tolerate this). |
| Filed an issue, then a later pass re-surfaces the same finding | Session state includes filed-issue URLs; auto-suppress and surface the filed URL as the rationale. |

---

## Things This Skill Does NOT Do

- **Review other people's PRs.** Author check is mandatory.
- **Persist session state across runs.** Push-backs and skips reset every invocation. This is intentional — a fresh session is a fresh perspective.
- **Post push-back rationale back to the PR as a comment.** Rationale stays in the local summary.md.
- **Consult closed issues.** Related-issues cache is `--state open` only. Closed history is noise.
- **Auto-run on `git push` via a hook.** User invokes explicitly.
- **Auto-ship on loop completion.** Standalone modes exit reporting the PR URL; pre-pr mode hands back to `issue-work` Phase 4.3's gate. In neither case does this skill push-and-merge without approval.
- **Skip hooks (`--no-verify`) or bypass signing.**
- **Add AI-attribution trailers** to commits.
- **Modify `impl-reviewer`'s lens semantics.** We pass it two extra cache paths; its review protocol is unchanged.
- **Run against `main`/`master`.** Phase 0.4 blocks this by requiring an open PR (standalone) or a non-trunk branch (pre-pr).

---

## References

- [references/triage-ui.md](references/triage-ui.md) — per-finding prompt shape, batch fallback, and suppression-key format

## Related Agents

- `impl-reviewer` — the three-lens reviewer, reused as-is. See `agents/impl-reviewer.md`.
- `archivist` — invoked in parallel during Phase 1.2 for related-notes discovery.

## Related Skills

- `issue-work` — delegates Phase 4 here via `pre-pr` mode.
- `issue-create` — invoked for `issue` triage action; handles dedup + filing.
- `ship` — invoked by `issue-work` Phase 4.3 after this skill returns (not by this skill directly).
- `agent-workspace` — trunk-root resolution for `.notes/` access from a worktree.
