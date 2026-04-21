---
name: workday-planning
description: Plan the workday by pulling context from user-configured sources (Google Docs, GitHub, Obsidian, URLs), handing synthesis to forge, and writing the day's plan to the personal vault. Day-of-week adaptive (Mon = week-prep, Fri = week-wrap). Triggers on "plan my day", "plan the workday", "morning plan", or the `/plan-workday` slash command.
---

# Workday Planning

Pull live context from the user's tracked projects (Google Docs, GitHub issues, Obsidian notes, web URLs), synthesize what's relevant to this week, get goal suggestions from forge, and write the day's plan to the user's personal vault.

**Planning artifacts live in the personal vault (second-brain by default), never in a project repo's `.notes/`.** Sources can be read from anywhere — project vaults, GitHub orgs, Google Drive — but the daily plan output is always personal / cross-cutting, so it belongs in the personal vault alongside other planning notes.

## When to Use

- User says "plan my day", "let's plan today", "plan the workday", "morning plan"
- `/plan-workday` slash command
- Monday morning (day also adds a week-prep overlay)
- Friday afternoon (day also adds a week-wrap overlay)

## Quick Reference

```
/plan-workday                  # auto-detect mode from day-of-week
/plan-workday --mode=day       # force daily plan (no overlays)
/plan-workday --mode=week-prep # force Monday week-prep overlay + day plan
/plan-workday --mode=week-wrap # force Friday week-wrap overlay + day plan
/plan-workday --edit-sources   # jump straight to editing planning-sources.md
```

---

## Config: `~/.claude/athena/planning-sources.md`

User-owned, editable by hand, bootstrapped by this skill on first run. Format:

```markdown
---
output_folder: Daily         # where daily plans land inside the personal vault. Default: Daily
projects:
  - name: Project Alpha
    sources:
      - type: google-doc
        id: 1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCdEfG
        label: Sprint Bikerack
        scan: most-recent:2      # current + prior sprint blocks
      - type: github-project
        owner: example-org
        number: 1
        status: "In progress"    # optional: filter to one status column
      - type: github-issues
        repo: example-org/example-repo
        filter: "assignee:@me state:open"
      - type: obsidian
        vault: second-brain
        path: "Journal/*-weekly-plan.md"
        scan: most-recent
  - name: Project Beta
    sources:
      - type: github-issues
        repo: example-org/another-repo
        filter: "state:open"
---

# Planning Sources

Freeform notes the user may add (reminders, context, scan-depth tweaks). The
skill only reads the frontmatter; this body is for the user's eyes.
```

### Source types

| `type`            | Required fields                       | Optional fields       | Fetched via                                              |
|-------------------|---------------------------------------|-----------------------|----------------------------------------------------------|
| `google-doc`      | `id` (or `url`), `label`              | `scan`                | Drive MCP `read_file_content`                            |
| `github-issues`   | `repo`, `filter` (gh search)          | `scan`                | `gh issue list --repo <r> --search "<f>"`                |
| `github-prs`      | `repo`, `filter` (gh search)          | `scan`                | `gh pr list --repo <r> --search "<f>"`                   |
| `github-project`  | `owner`, `number` (project number)    | `status`, `limit`     | `gh project item-list <n> --owner <o> --format json`     |
| `obsidian`        | `vault`, `path` (glob)                | `scan`, `include_hidden` | Glob + Read                                           |
| `url`             | `url`, `label`                        | `scan`                | WebFetch                                                 |

**`github-project` note.** Requires `gh` with the `read:project` scope. If the scope is missing, fetch will fail with `authentication token is missing required scopes [read:project]` — treat as a Phase 2 source failure and surface the fix command (`gh auth refresh -s read:project`) in the halt-and-ask prompt.

If `status` is provided, filter returned items to that exact status string (e.g., `"In progress"`, `"Todo"`, `"In review"`). If `limit` is provided, pass it through; otherwise default to `50`.

**`obsidian` note — hidden-dir exclusion.** Obsidian hides dot-prefixed directories (`.obsidian/`, `.trash/`, `.agents/`, etc.) from its UI. The skill mirrors that semantic: glob matches **exclude** any path component starting with `.` by default. This matters because `.agents/` holds agent working files (e.g., `.agents/forge/today.md`) — feeding forge's own plan back in as planning context creates a feedback loop. Set `include_hidden: true` on the source to override, only when you actually want to scan agent state.

**Filter mechanism.** `Glob` does not skip dot-prefixed directories on its own. After the glob returns, post-filter the result list: drop any path where **any** segment (split on `/`) starts with `.`. Apply this filter unless the source sets `include_hidden: true`. Example: `second-brain/Journal/.trash/old.md` has a `.trash` segment → drop; `second-brain/Journal/2026-04-21.md` has no dot-prefixed segment → keep.

If the user's glob itself targets a dotted directory (e.g., `path: ".trash/*"`), they must also set `include_hidden: true` — otherwise every match is filtered out.

### Scan modes

- `most-recent` (default) — for docs with sprint/date headings, grab the top-most section; for obsidian globs, grab the newest file; for issue lists, updated in the last 7 days.
- `most-recent:N` — same as `most-recent` but pull the top N sections / newest N files instead of just one. Example: `most-recent:2` on the bikerack pulls the current + prior sprint blocks for continuity.
- `whole-doc` — read the entire thing.
- `heading:<anchor>` — pull a specific section by heading match (substring or `startsWith`).
- `last-week` — for issue/PR lists, items updated in the last 7 days regardless of filter.

---

## Output Location

The daily plan is always written to the **personal vault**. The path is built from three values:

```
{notes_root}/{personal_vault}/{output_folder}/{YYYY-MM-DD}-daily-plan.md
```

- `notes_root` — from `~/.claude/athena/identity.md` (default `~/notes`)
- `personal_vault` — from `~/.claude/athena/identity.md` (default `second-brain`)
- `output_folder` — from the **top-level `output_folder` key** in `~/.claude/athena/planning-sources.md` frontmatter (default `Daily`)

Typical resolved path: `~/notes/second-brain/Daily/2026-04-21-daily-plan.md`.

**Create the output directory silently if it doesn't exist.** Don't ask.

### Setting or changing `output_folder`

In `planning-sources.md` frontmatter, add a top-level key alongside `projects:`:

```yaml
---
output_folder: Daily    # or Work, Projects, Plans, etc. Flat? use "." or omit for vault root.
projects:
  - name: ...
---
```

If missing, bootstrap asks the user which folder to use (default `Daily`) and writes it into the config.

### Why not a project `.notes/` or `forge/today.md`?

- Daily planning is cross-cutting by nature — goals come from multiple projects.
- Project `.notes/` is for notes *about that project*. A daily plan that spans five projects doesn't belong in any one of them.
- Forge's `.notes/.agents/forge/today.md` is forge's **internal working state** (completion tracking during the day), which may be useful but isn't the canonical daily plan. The skill owns the canonical file in the personal vault.

---

## Execution

### Phase 0 — Resolve mode, vault, and output path

1. Read `~/.claude/athena/identity.md`. Resolve:
   - `{{TIMEZONE}}` — must be an IANA zone string (e.g. `America/New_York`, `Europe/London`, `UTC`). **Validate before using** (see below). If missing or invalid, warn and fall back to system TZ — don't block planning on a config nit.
   - `{{PERSONAL_VAULT}}` (fall back to `second-brain`).
   - `{{NOTES_ROOT}}` (fall back to `~/notes`).
2. Read `~/.claude/athena/planning-sources.md` frontmatter's top-level `output_folder` (fall back to `Daily`). If the file is missing, defer to Phase 1 bootstrap.
3. **TZ validation.** Before shelling, check `{{TIMEZONE}}` matches `^(UTC|[A-Za-z][A-Za-z0-9_+-]*/[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z][A-Za-z0-9_+-]*)?)$` (IANA shape: `Region/City` or `Region/Country/City`, or bare `UTC`). Abbreviations like `EST` or `PT` fail this check — they also don't handle DST correctly. On mismatch, warn once (`⚠️ Identity TZ "{value}" is not an IANA zone — falling back to system TZ. Fix via /athena-setup.`) and proceed with the unset `TZ` env var so `date` uses the system default. This is also the injection guard: a validated value is safe to interpolate into the `TZ=...` shell command.
4. Compute today's day-of-week in the resolved timezone via `date` (Bash: one bare command, e.g. `TZ="{{TIMEZONE}}" date +%A` when validated, or plain `date +%A` on fallback).
5. Mode:
   - `--mode=<x>` flag wins.
   - Else: **Mon** → `week-prep`; **Tue–Thu** → `day`; **Fri** → `week-wrap`; **Sat/Sun** → `day` (tell the user it's a weekend, ask if they want to proceed anyway).
6. Compute output path: `{{NOTES_ROOT}}/{{PERSONAL_VAULT}}/{{output_folder}}/{YYYY-MM-DD}-daily-plan.md`. Create the output directory if missing (silent; don't ask). If `output_folder` is `.`, write at vault root with the date-prefixed filename.
7. Print one line: `Mode: {mode} (today is {Monday 2026-04-21}) → will write {output path}`.

### Phase 1 — Load or bootstrap `planning-sources.md`

1. Check `~/.claude/athena/planning-sources.md`:
   - **Missing** → run the [Bootstrap Flow](#bootstrap-flow) below, then continue.
   - **Present but empty `projects:` list** → offer to bootstrap now or skip and use a generic "what are you working on?" prompt.
   - **Present and populated** → parse the YAML frontmatter into a project list.
2. Print one line: `Loaded N projects, M total sources.`

### Phase 2 — Fetch sources (parallel; halt-and-ask per failure after collection)

Fetch every source in parallel (one tool call per source, batched in a single message). Wait for all results, then for each failure halt and prompt the user before continuing to Phase 3:

```
⚠️ Source failed: {project} / {label or type}
Reason: {error}

Continue without this source, or fix and retry?
```

Use AskUserQuestion. Options:

- **Continue** — mark this source skipped for this run; note in footer.
- **Retry** — re-run the fetch (e.g., user just fixed auth).
- **Edit sources** — open `planning-sources.md` for editing; abort this run.
- **Abort** — stop the skill.

If two or more sources failed, add a fifth option on the second-and-subsequent prompts: **Skip all remaining failures** — mark every outstanding failed source as skipped (footer-logged) and jump to Phase 3.

Do not silently skip without the user's go-ahead. The user asked for halt-and-ask on failure.

### Phase 3 — Synthesize per project

For each project, produce a compact block:

```markdown
## {Project Name}

**New / changed** (since last Mon, or last 7 days):
- {bullet}

**Open & assigned to you:**
- {bullet}

**Decisions needed:**
- {bullet}

**Stale / risk:**
- {bullet}
```

Omit empty sections. Keep each bullet one line. This is context for forge, not a report for the user to read in full.

### Phase 4 — [Monday only] Week-prep overlay

Prepend this before the daily plan:

```markdown
## 📅 Week Prep — Week of {YYYY-MM-DD}

### Last week
{1-3 lines on last week's wins/drops. To locate the prior week's forge
session archive, delegate to archivist with the **list of configured
project names from Phase 1** so it knows which `.notes/` roots to search:
`Task(subagent_type="archivist", prompt="Search these projects' .notes/.agents/forge/sessions/
directories for the most recent forge session archive: {comma-separated project
names}. Return its content, or 'no match' if none found.")`. Don't resolve
.notes/ paths directly — archivist handles worktree + project-vault routing.
If archivist returns no match, use "No prior week on record."}

### This week's shape
{2-4 lines synthesizing cross-project commitments, deadlines, and stated
priorities from the Phase 3 synthesis. This is the week's thesis — what
would make it a good week?}

### Standing commitments
{Recurring meetings, known deadlines, deliverables — pulled from sources
if surfaced, otherwise ask the user to confirm what's on the calendar.}
```

Do NOT run `/weekly-planning`. This is a lightweight prepend, not the full VOMIT Q&A. The user can invoke weekly-planning separately if they want the Q&A flow.

### Phase 5 — Get goals from forge

Invoke forge with the synthesis as context. **Tell forge to return goals only — the workday-planning skill owns the file write, forge should not also write to its own `today.md` during this flow.**

```
Task(
  subagent_type="forge",
  prompt="""
  Plan today's goals. Goal mode.

  Forge context (from workday-planning skill):
  {Phase 3 synthesis, compact}

  {If Monday: the week-prep overlay from Phase 4}

  Surface 3-5 goals. Prioritize items the user explicitly committed to
  or that are blocking others. Don't promote everything in the synthesis —
  let the user choose.

  IMPORTANT: return goals as text only. Do NOT write to .notes/.agents/forge/today.md
  — the workday-planning skill owns the canonical daily plan file and will persist it
  to the personal vault at {output path from Phase 0}.
  """
)
```

Capture forge's goal list for Phase 7 (write).

> **Note — tracked in [#6](https://github.com/SnowboardTechie/athena-notes/issues/6).** The prompt-level "don't write today.md" override is a temporary coupling. Once forge accepts an output-path parameter, this skill will pass the resolved path instead of instructing forge to skip its default write.

### Phase 6 — [Friday only] Week-wrap overlay

Compute this **before** the Phase 7 write so the overlay can be embedded in the final file. Use the template:

```markdown
## 🏁 Week Wrap — Week of {YYYY-MM-DD}

### Wins
{Delegate to archivist to pull entries from .notes/.agents/forge/wins.md
since Monday (`Task(subagent_type="archivist", prompt="Return entries from
.notes/.agents/forge/wins.md dated since {last Monday YYYY-MM-DD}")`) —
archivist owns .notes/ path resolution. Combine with any completed items
surfaced in Phase 3 synthesis.}

### Dropped
{Carry-overs from earlier this week that didn't land. Ask the user to
confirm if not obvious from forge archive.}

### Carry forward to next week
{What goes onto next Monday's week-prep. User picks.}

### Patterns
{One line the user wants to remember — what worked or didn't. Optional.}
```

Ask the user to fill in any sections the archive can't answer. Keep it short; this is a weekly cap, not a retrospective.

### Phase 7 — Write the daily plan

Assemble the daily plan file at the output path from Phase 0 with this structure:

```markdown
---
date: {YYYY-MM-DD}
mode: {day | week-prep | week-wrap}
type: daily-plan
sources: {N sources, M succeeded}
---

# Daily Plan — {Weekday}, {Month D, YYYY}

{If Monday: paste the Phase 4 week-prep overlay here}

## 🎯 Goals

{Forge's goal list, verbatim}

### Start here

{Forge's "Start here" block}

### Likely obstacles

{Forge's obstacles block, if any}

---

## Source synthesis

{Phase 3 per-project blocks — for reference / deeper dive if needed}

{If Friday: paste the Phase 6 week-wrap overlay here, computed before this write}

---

## Meta

- Sources fetched: {list with ✅ / ⚠️ status}
- Skipped sources: {any Phase 2 skips with reasons, or "none"}
- Generated by workday-planning skill on {YYYY-MM-DD HH:MM {TZ}}
```

Write via the Write tool. If the file already exists (user ran planning twice the same day), show a one-line summary of what would change and ask **Overwrite** or **Keep existing** (2-choice). No merge option — merging two plans has too many undefined cases (which goals win? which synthesis?) and would hide the fact that a plan was regenerated.

### Phase 8 — Present

Print in this order:

1. Mode + date header (one line).
2. Week-prep overlay (Monday only).
3. Per-project synthesis (Phase 3 blocks).
4. Forge's daily plan (verbatim from Task return).
5. Week-wrap overlay (Friday only).
6. Footer: any `⚠️ Sources unavailable` notes from Phase 2 skips.

---

## Bootstrap Flow

Triggered when `planning-sources.md` is missing, or on `--edit-sources`.

### Step 1 — Intro

```
No planning sources file yet. Let's build one.

I'll ask a few questions to populate ~/.claude/athena/planning-sources.md.
You can edit it directly after (it's just markdown + YAML). Takes ~3 minutes.
```

### Step 1.5 — Output folder

Ask (AskUserQuestion):

```
Where should daily plans live inside ~/notes/{personal_vault}/?
  - Daily          (default, temporal bucket)
  - Work           (work-day plans, separate from personal projects)
  - Projects       (broader — covers any project work)
  - Custom         (user types a folder name; enter "." for flat at vault root)
```

Save the choice as `output_folder` at the top of the frontmatter.

### Step 2 — Projects

Ask: `What projects do you want to plan against? (List them, one per line.)`

For each project:

### Step 3 — Sources per project

Loop per project. AskUserQuestion caps at 4 options per call — pre-group the 7 source types into two tiered questions so the user doesn't face an ad-hoc split each loop.

**Call 1 — pick a category:**

```
question: "Add a source for {project}? (pick a category, or 'done')"
options:
  - label: "GitHub"       description: "Issues, PRs, or a Projects V2 board"
  - label: "Documents"    description: "Google Doc, URL, or Obsidian note(s)"
  - label: "Done with this project"
```

**Call 2 — pick the specific type** (only if category chosen above):

If "GitHub":
```
options:
  - label: "GitHub issues"    description: "Repo + filter (e.g. 'assignee:@me state:open')"
  - label: "GitHub PRs"       description: "Repo + filter"
  - label: "GitHub Project"   description: "Projects V2 board (owner + project number)"
```

If "Documents":
```
options:
  - label: "Google Doc"       description: "Paste a docs.google.com URL or doc ID"
  - label: "Obsidian note(s)" description: "Vault + path/glob"
  - label: "URL"              description: "Any web page"
```

Follow-up prompts by type:

- **Google Doc** — ask for URL or ID; extract ID from URL; ask for a short label; ask scan mode (default `most-recent`, offer `most-recent:N` or `whole-doc`).
- **GitHub issues/PRs** — ask for `owner/repo`; ask for `gh search` filter (default `"assignee:@me state:open"`).
- **GitHub Project** — ask for owner (org or user) + project number (e.g., `17`). Optional: a status filter (e.g., `"In progress"`) and an item limit (default 50). If the user pastes a URL like `https://github.com/orgs/HHS/projects/17`, parse owner + number from it.
- **Obsidian** — ask for vault name (default from `identity.md` `personal_vault`); ask for path/glob; ask scan mode.
- **URL** — ask for URL and label.

### Step 4 — Confirm & write

Show the generated YAML frontmatter and ask: `Write this to ~/.claude/athena/planning-sources.md? [Y/n]`

If yes, write the file with frontmatter + a brief markdown body explaining the user can edit freely. Create `~/.claude/athena/` if missing.

### Step 5 — Continue or stop

Ask: `Sources saved. Continue with today's planning, or stop here?`

If continue, proceed to Phase 2 with the new config.

---

## Tone & Shape

- **Terse.** Synthesis blocks are one-line bullets. Overlays are 2-4 lines per subsection.
- **Forge does the goals.** This skill fetches and synthesizes; goal prioritization is forge's job. Don't write a parallel goal list here.
- **Halt loudly on source failure.** The user asked for halt-and-ask, not silent skip. A broken source is a signal, not noise.
- **Monday is not a retrospective.** Week-prep is a lightweight prepend, not the VOMIT Q&A. Direct the user to `/weekly-planning` if they want depth.

---

## Edge cases

**No `planning-sources.md` and user wants to skip bootstrap:**
Offer to run in "ad-hoc" mode — ask "what are you working on today?" and feed the answer to forge without doc synthesis. Don't force the config flow.

**Weekend:**
Default mode is `day` with a one-line acknowledgment: `Today is Saturday — not a typical workday. Proceed?`

**Day-of-week override mismatch:**
If the user passes `--mode=week-wrap` on a Tuesday, run the overlay anyway — user override wins. Print one line: `Running week-wrap overlay on Tuesday (override).`

**Forge returns `forge_available: false` or task errors:**
Fall back to presenting the Phase 3 synthesis + a manual "what will you tackle today?" prompt. Don't block the session on forge being unreachable.

**Source config references an unknown type:**
Halt with: `Unknown source type '{x}' in {project}. Edit ~/.claude/athena/planning-sources.md and rerun.` Don't guess.

**Malformed YAML frontmatter in `planning-sources.md`:**
If parsing fails, halt with the parser error and the offending line if available:
`Could not parse frontmatter in ~/.claude/athena/planning-sources.md: {error}. Fix the file or run /plan-workday --edit-sources.` Do NOT fall back to bootstrap — that would overwrite the user's in-progress edit. Do NOT guess at the intended shape.

**Drive MCP not authed (Google Doc fails):**
Treat as a source failure in Phase 2. The halt-and-ask prompt will let the user fix auth and retry, skip the source, or abort.

**`gh` missing `read:project` scope (github-project fails):**
Surface the exact fix in the halt-and-ask prompt:
```
⚠️ Source failed: {project} / GitHub Project {owner}/{number}
Reason: authentication token is missing required scopes [read:project]

Fix: run `gh auth refresh -s read:project` in another terminal, then pick Retry.
```
Continue / Retry / Edit sources / Abort as usual.

**Running non-interactively (as a scheduled routine):**
If no TTY / user not present, a source failure should still abort (not silently continue). The operator can review the halt message after the fact and re-run. This is intentional — the user doesn't want stale or partial planning sneaking through.

---

## Dependencies

- **forge** — goal-mode planning; owns `today.md`. This skill currently instructs forge via prompt to skip the `today.md` write; tracked for replacement with an output-path parameter in [#6](https://github.com/SnowboardTechie/athena-notes/issues/6).
- **scout** — (optional) forge activity summary; forge invokes scout automatically when planning
- **Drive MCP** (optional) — required only if `google-doc` sources are configured
- **`gh`** (optional) — required only if `github-*` sources are configured
- **Obsidian skill** — vault path conventions for `obsidian` sources

---

## Guardrails

- Do NOT write user-specific project names, URLs, or doc IDs into this skill body — they belong in `planning-sources.md`.
- Do NOT auto-chain `/weekly-planning` on Mondays — the overlay is the Monday mode. User invokes weekly-planning separately if desired.
- Do NOT silently skip failed sources. Always halt-and-ask.
- Do NOT write the daily plan into a project `.notes/` or any project-scoped location. **The daily plan always lives in the personal vault**, at `{notes_root}/{personal_vault}/{output_folder}/`.
- Do NOT let forge write its `.notes/.agents/forge/today.md` during this flow — tell forge "return goals as text only" in the Task prompt. The workday-planning skill owns the canonical daily-plan file.
- Do NOT re-run bootstrap if the file exists and has projects, even if sources look thin. Suggest `--edit-sources` instead.
- ALWAYS print the mode and date on the first line of output so the user can see what flow they're in.
