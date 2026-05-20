---
name: agent-workspace
description: Working directory conventions for cairn-notes skills and spokes — task context, drafts, research cache in .notes/.agents/. Includes worktree-aware .notes path resolution and auto-setup of project vaults.
---

# Agent Workspace — Working Directory Conventions

This skill defines how agents use the `.notes/.agents/` directory for working state, drafts, and ephemeral context that isn't ready for permanent notes. It also provides the worktree-aware protocol for resolving the correct `.notes/` path in any working directory.

## Philosophy

- **`.notes/` = Permanent knowledge** — ideas, explorations, decisions worth keeping
- **`.notes/.agents/` = Working state** — task context, drafts, research cache that lives until task completion

The `.agents/` prefix keeps working files separate from permanent notes while allowing them to coexist in the same vault (Obsidian treats dot-folders as hidden by default).

---

## Directory Structure

```
.notes/.agents/
├── {skill}/                 # Per-skill working state (long-running task pattern)
│   └── {task-slug}/
│       ├── context.md       # Task context and goals
│       ├── progress.md      # What's been explored/decided
│       └── threads.md       # Open threads to pursue
│
├── sage/                    # Sage's research cache
│   └── {topic-slug}/
│       ├── findings.md      # Synthesized findings
│       └── sources.md       # Raw source links/excerpts
│
├── archivist/               # Archivist's search context
│   └── recent-searches.md
│
├── forge/                   # Forge's deep work state
│   ├── today.md
│   ├── sessions/            # Archived daily sessions
│   └── wins.md              # Completed blocks (momentum)
│
├── kindle/                  # Kindle's flow-barrier tracking
│   ├── patterns.md
│   └── sessions/
│
├── drafts/                  # Notes not ready for .notes/
│   └── {draft-name}.md
│
└── _archive/                # Completed task context (optional)
    └── {date}-{task-slug}/
```

The `{skill}/{task-slug}/` shape at the top is the **long-running task pattern** — any skill that wants per-task state (context + progress + open threads across multiple sessions) writes to its own namespaced subdir. Per-skill top-level files (like `forge/today.md`) work alongside it.

---

## File Conventions

### Task Context (`{skill}/{task-slug}/context.md`)

```markdown
---
task: {task-slug}
created: YYYY-MM-DD
status: active | paused | complete
---

# Task: {Title}

## Goal
{What are we trying to accomplish?}

## Scope
- In scope: {what's included}
- Out of scope: {what's excluded}

## Context
{Background, constraints, relevant notes}

## Related Notes
- [[{existing note}]]
```

### Task Progress (`{skill}/{task-slug}/progress.md`)

```markdown
---
task: {task-slug}
updated: YYYY-MM-DD
---

# Progress: {Title}

## Completed
- [x] {What's been done}

## In Progress
- [ ] {Current focus}

## Insights So Far
- {Key insight}

## Open Questions
- {Question to resolve}

## Next Steps
- {What to do next}
```

### Research Cache (`sage/{topic-slug}/findings.md`)

```markdown
---
topic: {topic-slug}
researched: YYYY-MM-DD
expires: YYYY-MM-DD  # Optional TTL
confidence: high | medium | low
---

# Research: {Topic}

## Summary
{2-3 sentence synthesis}

## Key Findings

### From Web
- **{Source}**: {finding}

### From Docs
- {Official guidance}

### From Code
- **{repo}**: {pattern found}

## Gaps
- {What couldn't be verified}

## Raw Sources
{Links, excerpts for reference}
```

### Draft Notes (`drafts/{name}.md`)

```markdown
---
draft: true
created: YYYY-MM-DD
target: idea | exploration | decision  # What it might become
---

# Draft: {Title}

{Content being developed}

## Notes to Self
- {What needs more work}
- {Questions to resolve before promoting}
```

---

## Lifecycle Rules

### Task-scoped content

| Phase | Action |
|---|---|
| Task starts | Create `{task-slug}/context.md` |
| During work | Update `progress.md`, add `threads.md` |
| Task complete | Archive to `_archive/` OR delete |
| Insights emerge | Promote to permanent note via scribe |

### Research cache

| Condition | Action |
|---|---|
| Topic researched | Create `sage/{topic}/findings.md` |
| Re-researching same topic | Update existing, note date |
| Topic stale (>30 days) | Consider refreshing or deleting |
| Task complete | Delete unless useful for future |

### Drafts

| Condition | Action |
|---|---|
| Idea forming | Create draft in `drafts/` |
| Draft ready | Promote to `.notes/` via scribe |
| Draft posted / promoted | Archive to `_archive/{domain}/` with canonical-artifact footer (see Archive Pattern below) |
| Draft abandoned | Delete via pyre |
| Draft stale (>14 days) | Review — promote, archive, or delete |

---

## Archive Pattern

When a draft or task artifact reaches a "done" state — posted as an issue, promoted to a permanent note, shipped as a PR — the working file should be **archived**, not deleted. The archive preserves the thinking that led to the canonical artifact, which is useful for retros and future grep.

### Path convention

```
.notes/.agents/_archive/{domain}/{YYYY-MM-DD}-{slug}.md          # single file
.notes/.agents/_archive/{domain}/{YYYY-MM-DD}-{slug}/             # multi-file work
```

- `{domain}` — the skill or workflow that produced the artifact (e.g., `issue-create`, `weekly-planning`, `session-review`). Keeps archives browsable by skill.
- `{YYYY-MM-DD}` — the date the artifact was posted/promoted, in the user's local timezone. Makes chronological browsing trivial.
- `{slug}` — the same slug used in the original `drafts/` filename (lowercased title, non-alphanumerics → `-`).

### Footer convention

Archived files should end with a minimal "where this went" footer so the file explains itself without reaching for context:

```markdown
---
Posted: https://github.com/owner/repo/issues/123
```

Or for promoted notes:

```markdown
---
Promoted: [[my-published-note]]
```

One canonical artifact per archive file. If the draft produced multiple outputs (e.g., an idea split into two tickets), record both with separate lines.

### When to archive vs. delete

| Condition | Action |
|---|---|
| Draft posted/promoted successfully | Archive |
| Draft explicitly abandoned by user | Delete via pyre |
| Half-finished scratch work the user says to drop | Delete via pyre |
| Draft older than 14 days and never promoted | Review with user — promote, archive, or delete |
| Task context for completed work (`{skill}/{task-slug}/`) | Archive if there are non-trivial insights; otherwise delete |

**Default to archive** when a draft produced an artifact. Deletion is reserved for work the user has explicitly walked away from.

### Pyre integration

`pyre` is the only agent that should delete files under `.agents/`. Its standard tiered-confirmation rules apply to `_archive/` too — archived work is no less sensitive than an active draft just because it's been moved.

---

## Agent Responsibilities

### Scribe (only writer)

- Writes task context files to `.agents/{skill}/{task}/` when a calling skill uses the long-running task pattern
- Writes drafts to `.agents/drafts/`
- Promotes drafts to `.notes/` when ready
- Updates progress files

### Sage

- Caches research findings in `.agents/sage/{topic}/`
- Checks cache before re-researching same topic
- Updates findings with new research
- Notes confidence and freshness

### Archivist

- Searches both `.notes/` AND `.notes/.agents/` for context (honors the `scope:` keyword to narrow)
- Prioritizes permanent notes over working state
- Reports working state separately ("Also found in working files...")

### Pyre

- Cleans up `.agents/` content when tasks complete
- **Relaxed confirmation** for ephemeral files (task context, cache)
- **Normal confirmation** for drafts (might have valuable content)
- Archives to `_archive/` if requested instead of deleting

### Forge / Kindle

- Each writes to its own subdirectory (`.agents/forge/`, `.agents/kindle/`)
- Session state is ephemeral; patterns/wins are append-only

### Calling skills

- Skills that orchestrate long-running tasks (issue-work, planning skills) own their own `.agents/{skill}/` subdir
- Task lifecycle (start / update progress / complete / cleanup) is the skill's job, not a spoke's — the skill delegates the actual file writes/deletions to scribe and pyre

---

## Worktree-Aware Resolution (critical)

**Agents may operate inside a git worktree.** Worktrees share the same git object store but have separate working directories. The `.notes` symlink lives in the **trunk** (main worktree), not in each worktree.

### Why this matters

`git rev-parse --show-toplevel` returns the **worktree** path, not the trunk path. Without worktree detection, agents would:
- Create separate `.notes` per worktree (e.g., `~/notes/myapp.feat-auth/`)
- Lose access to shared project notes
- Fragment the notes system

### Detection

In a worktree, `.git` is a **file** (contains `gitdir:` pointer). In the trunk, `.git` is a **directory**.

```bash
if [ -f "$(git rev-parse --show-toplevel)/.git" ]; then
  IS_WORKTREE=true
else
  IS_WORKTREE=false
fi
```

### Resolving the trunk root

Always use this function (or equivalent logic) instead of `git rev-parse --show-toplevel` directly:

```bash
resolve_trunk_root() {
  local toplevel
  toplevel=$(git rev-parse --show-toplevel)

  if [ -f "${toplevel}/.git" ]; then
    # In a worktree — resolve trunk from git common dir
    local common_dir
    common_dir=$(git rev-parse --git-common-dir)
    # common_dir is like /path/to/trunk/.git — parent is the trunk root
    dirname "$common_dir"
  else
    # In the trunk
    echo "$toplevel"
  fi
}

TRUNK_ROOT=$(resolve_trunk_root)
PROJECT_NAME=$(basename "$TRUNK_ROOT")
```

### Rules

| Scenario | `git rev-parse --show-toplevel` | `resolve_trunk_root` | `.notes` location |
|---|---|---|---|
| In trunk `myapp/` | `~/code/myapp` | `~/code/myapp` | `~/code/myapp/.notes` |
| In worktree `myapp.feat-auth/` | `~/code/myapp.feat-auth` | `~/code/myapp` | `~/code/myapp/.notes` |
| In worktree `myapp.fix-bug/` | `~/code/myapp.fix-bug` | `~/code/myapp` | `~/code/myapp/.notes` |

**Key principle:** `.notes` is ONLY created in the trunk. All worktrees access the trunk's `.notes` by resolving `TRUNK_ROOT`.

---

## Auto-Setup Protocol

When an agent is invoked in a git repo and `.notes/` is missing. Use tool-native calls where possible; Bash is reserved for git queries, `mkdir -p`, and `ln -s` (single bare commands).

1. **Resolve the trunk root** (handles worktrees automatically) — Bash is required for `git rev-parse`:
   ```bash
   git rev-parse --show-toplevel
   ```
   Then check if it's a worktree via `git rev-parse --git-common-dir` (returns the trunk's `.git`). The parent of that path is `TRUNK_ROOT`. `PROJECT_NAME` is its basename.

2. **Check for existing `.notes/` in the trunk** — use **Glob**, not `ls`:
   ```
   Glob(pattern="{TRUNK_ROOT}/.notes")
   ```
   If it returns a result, `.notes` exists. To determine whether it's a symlink vs a regular directory, try `Glob(pattern="{TRUNK_ROOT}/.notes/*")` — if that returns files, check the invoking agent's intent (symlinks transparently resolve). If you truly need to distinguish, one bare `readlink {TRUNK_ROOT}/.notes` Bash call is acceptable (no chains).

3. **If missing, read `notes_root` from identity** — use **Read**, not `grep`:
   ```
   Read(file_path="~/.claude/cairn/identity.md")
   ```
   Parse the `notes_root:` field in your response; expand `~` to `$HOME`.

4. **Create target directory and symlink in the trunk** — Bash required (no tool equivalent). One command per call:
   ```bash
   mkdir -p {NOTES_ROOT}/{PROJECT_NAME}
   ```
   ```bash
   ln -s {NOTES_ROOT}/{PROJECT_NAME} {TRUNK_ROOT}/.notes
   ```

5. **Add to `.gitignore` if not present** — use **Read + Edit**, not `grep`/`echo`:
   ```
   Read(file_path="{TRUNK_ROOT}/.gitignore")
   ```
   If `.notes` isn't on a line by itself, use `Edit` to append it (or `Write` if the file doesn't exist yet).

6. **Confirm setup** to the user:
   ```
   Notes directory ready: {TRUNK_ROOT}/.notes -> {NOTES_ROOT}/{PROJECT_NAME}/
   ```

7. **If `.notes` exists as a regular directory (not symlink):**
   - **Stop.** Do not overwrite.
   - Report to user: ".notes/ exists as a regular directory. The plugin expects it to be a symlink. Please move its contents or rename before continuing."

**The setup is idempotent** — safe to run multiple times.

### Bash hygiene in this protocol

- `git rev-parse`, `mkdir -p`, `ln -s`, and (rarely) `readlink` are the only allowed Bash calls
- Each is a single bare command — no `&&`/`||`/`|`, no `2>/dev/null`, no `cd`, absolute paths only
- Never `ls`, `grep`, `find`, `cat`, `head`, `tail`, `echo` to file — use Glob / Grep / Read / Edit / Write

---

## Directory Initialization

When `.agents/` first needs to be used, create the structure:

```bash
mkdir -p .notes/.agents/{sage,archivist,forge,kindle,drafts,_archive}
```

If the notes target directory (e.g., `~/notes/{project}/`) doesn't have `.agents/`, it will be created on first write. No explicit init step needed.

---

## Personal Vault Auto-Create

When writing to the personal vault (`{NOTES_ROOT}/{PERSONAL_VAULT}/`) and it doesn't exist:

```bash
NOTES_ROOT=$(grep '^notes_root:' ~/.claude/cairn/identity.md | cut -d: -f2- | xargs)
PERSONAL_VAULT=$(grep '^personal_vault:' ~/.claude/cairn/identity.md | cut -d: -f2- | xargs)
NOTES_ROOT="${NOTES_ROOT/#\~/$HOME}"

mkdir -p "${NOTES_ROOT}/${PERSONAL_VAULT}"
```

Do this silently the first time. No prompt needed — user already configured this during `/cairn-setup`.

---

## Constraints

- Never write outside a resolved notes root
- Never delete files without user confirmation (pyre handles deletion with its own protocol)
- `.notes` must always be a symlink in a project repo — never a regular directory
- Worktrees must never have their own `.notes` — always resolve to the trunk's
- `.gitignore` additions should be minimal (just `.notes`) — don't pollute it
