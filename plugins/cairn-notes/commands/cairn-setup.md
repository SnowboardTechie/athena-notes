---
description: Onboarding flow for cairn-notes — writes ~/.claude/cairn/identity.md with user's name, vault config, working hours, and cognitive peak. Pre-fills from existing Claude Code memory where possible.
---

# /cairn-setup

You are running the cairn-notes onboarding flow. Your job: produce a valid `~/.claude/cairn/identity.md` file with minimal friction.

## Philosophy

- **Tell the user what you're doing before you do it.** Never read files or run commands without first saying what and why. Users should never face a permission prompt and wonder "why is this happening?"
- **Pre-fill, don't interrogate.** Scan existing Claude Code context first. Ask only what you can't infer.
- **Sensible defaults.** Every question has a default the user can accept with Enter.
- **5-7 questions max.** Anything more is a flaw in your discovery logic.
- **Confirm before writing.** Show the final identity file and ask for approval.
- **Show permissions verbatim.** When offering to add permissions to settings, show the exact list — never paraphrase as "necessary permissions."

---

## Phase 0: Introduce what's about to happen (MANDATORY FIRST OUTPUT)

Before any file reads or bash commands, print this intro so the user understands any permission prompts they're about to see:

```
Welcome to cairn-notes setup.

This will take about 2 minutes. Here's the plan:

  1. I'll scan your existing Claude Code setup (CLAUDE.md, memory files) for
     any identity info I can pre-fill — name, timezone, etc. You may see a
     few permission prompts for reading those files. None of this data leaves
     your machine.

  2. I'll ask 5-7 short questions about anything I couldn't infer.

  3. I'll show you the final identity before writing it to
     ~/.claude/cairn/identity.md.

  4. I'll offer to allowlist the permissions this plugin needs so you don't
     get interrupted every time an agent reads your notes or identity. I'll
     show you exactly what those permissions are before adding them.

Starting now.
```

Only after printing this intro do you proceed to Phase 1.

---

## Phase 1: Discovery

Tell the user what you're doing, then gather signals from these sources in parallel:

```
Scanning for existing identity info...
```

### 1.1 Existing Claude Code memory

Check for identity signals in:

- `~/.claude/CLAUDE.md` — global instructions (look for name, role, timezone)
- `~/.claude/memory/*.md` — user memory files (profile, voice, preferences)
- `~/.claude/projects/*/memory/*.md` — project-scoped memory files
- `~/.claude/projects/*/memory/MEMORY.md` — memory index pointing to relevant files

Read whatever exists. Extract: name, pronouns, timezone, working hours, vault preferences, role.

### 1.2 System signals

- `echo $TZ` or `date +%Z` — timezone (Bash: one bare command)
- `Glob(pattern="~/notes/*/")` — existing vault names (Glob, not `ls`)
- `echo $USER` — fallback for name (Bash: one bare command)

### 1.3 Existing identity file

If `~/.claude/cairn/identity.md` already exists, read it. This is a re-run, not a first-run. Show current values and ask which to update.

---

## Phase 2: Questions (only what's missing)

Use AskUserQuestion for each item. Pre-fill with discovered values. User can accept, edit, or skip.

### Required questions

**Q1: Your name**
- Default: from CLAUDE.md, memory files, or `$USER`
- Used by: forge, kindle, and other skills/spokes that address the user by name
- Example: "Jane Doe"

**Q2: Timezone**
- Default: from `$TZ`, `date +%Z`, or memory files (e.g., "Pacific timezone" → America/Los_Angeles)
- Used by: daily note timestamps, forge working hours
- Format: IANA timezone (America/Los_Angeles, America/New_York, Europe/London, etc.)

**Q3: Personal vault name**
- Default: `second-brain` (or first name in `~/notes/*/` if one exists)
- Used by: scribe routing for cross-project and personal notes
- Creates: `~/notes/{name}/` on first use if missing

**Q4: Notes root directory**
- Default: `~/notes`
- Used by: all vault path resolution
- Expand `~` when writing to identity file

**Q5: Working hours**
- Default from memory if present (e.g., "7:30am - 4pm PT" → start 07:30, end 16:00)
- Two sub-questions: start time (HH:MM), end time (HH:MM)
- Used by: forge for block scheduling and end-of-day detection

### Optional questions (offer to skip)

**Q6: Cognitive peak window**
- Default: first 2-3 hours of working day (matches most morning-person patterns)
- Two sub-questions: start time, end time
- Used by: forge to sequence hardest tasks into peak window
- Skip option: "Use default (first 2 hours of working day)"

**Q7: Pronouns / preferred address**
- Default: name only (no pronoun)
- Used by: skills/spokes that adapt conversational style when addressing the user
- Skip option: "Just use my name"

---

## Phase 3: Confirm

Before writing, show the full identity file and ask:

```
Here's your cairn-notes identity:

---
name: Jane Doe
timezone: America/Los_Angeles
notes_root: ~/notes
personal_vault: second-brain
working_hours:
  start: "07:30"
  end: "16:00"
cognitive_peak:
  start: "07:30"
  end: "10:00"
pronouns: she/her
---

Write this to ~/.claude/cairn/identity.md?
```

If approved, write. If not, ask which fields to change.

---

## Phase 4: Write

Write to `~/.claude/cairn/identity.md`:

```markdown
---
name: {{NAME}}
timezone: {{TIMEZONE}}
notes_root: {{NOTES_ROOT}}
personal_vault: {{PERSONAL_VAULT}}
working_hours:
  start: "{{WH_START}}"
  end: "{{WH_END}}"
cognitive_peak:
  start: "{{CP_START}}"
  end: "{{CP_END}}"
pronouns: {{PRONOUNS}}
---

# cairn-notes — User Identity

Generated by `/cairn-setup` on {{DATE}}.

Re-run `/cairn-setup` any time to update. Skills and spokes read this file at invocation — no restart needed.

## Fields

- **name** — for direct address by skills and spokes that greet by name
- **timezone** — IANA timezone for daily notes, timestamps, working-hour detection
- **notes_root** — root directory for all vaults
- **personal_vault** — default vault for cross-project / personal notes
- **working_hours** — start/end in 24-hour format; forge uses this for block planning
- **cognitive_peak** — when you do your best analytical work; forge sequences hardest tasks here
- **pronouns** — optional; for natural conversational style
```

Also ensure `~/.claude/cairn/` directory exists. Create it if missing.

---

## Phase 5: Offer to configure permissions (new user convenience)

Without this, the user will hit a permission prompt for almost every operation. Offer to configure Claude Code's `permissions.defaultMode: "auto"` (official research-preview mode that auto-approves routine ops while still enforcing deny rules and background safety checks).

### 5.0 Resolve paths to absolute before rendering

**Critical.** Claude Code does not reliably expand `~` inside permission patterns — entries like `Read(~/notes/**)` silently never match, so every read still prompts. Before rendering or writing any entries, compute:

- `NOTES_ROOT_ABS` — `notes_root` from identity, with `~` replaced by `$HOME` (e.g., `/Users/bryan/notes`). If already absolute, use as-is.
- `CAIRN_HOME_ABS` — `$HOME/.claude/cairn` (always absolute).

Use `echo $HOME` via Bash if you need to resolve `$HOME`. All subsequent entries reference these resolved values, never `~`.

### 5.1 Explain verbatim before asking (DO NOT PARAPHRASE)

**Print the block below EXACTLY as written**, substituting `{NOTES_ROOT_ABS}` and `{CAIRN_HOME_ABS}` with the resolved absolute paths from 5.0. Do NOT summarize this as "necessary permissions" — show the actual config. Users should see every entry before approving.

```
───────────────────────────────────────────────────────────────
Permission configuration

cairn-notes needs to read, search, and write across your notes folders
and identity file without constant prompting. The cleanest way to do
this uses Claude Code's built-in "auto" permission mode (research preview)
plus a narrow deny list for genuinely dangerous operations.

If you approve, I'll set these values in ~/.claude/settings.json:

  defaultMode: "auto"
    → Auto-approves routine tool calls with background safety checks.
      Deny rules are still enforced; auto mode does NOT disable safety.

  allow — notes/identity paths (14 entries, every tool the spokes use):

    Notes vault ({NOTES_ROOT_ABS}/**):
      • Read, Write, Edit   — load, save, update notes
      • Glob, Grep          — find notes by filename or content

    Identity file ({CAIRN_HOME_ABS}/**):
      • Read, Write, Edit   — load/update identity on re-run
      • Glob                — existence checks

    Project-local view (.notes/**, symlink inside each repo):
      • Read, Write, Edit, Glob, Grep

  allow — Bash shapes the spokes need (9 entries):
    • Bash(git rev-parse:*)            — resolve trunk vs. worktree
    • Bash(mkdir:*)                    — create vault directory on first use
    • Bash(ln:*)                       — create the .notes symlink
    • Bash(readlink:*)                 — inspect the .notes symlink
    • Bash(rm .notes/**:*)             — pyre file deletion (scoped to vault)
    • Bash(rm -r .notes/.agents/**:*)  — task-cleanup recursive (working state only)
    • Bash(echo:*)                     — identity discovery ($USER, $TZ, $HOME)
    • Bash(date:*)                     — timezone discovery
    • Bash(test:*)                     — file/symlink existence checks

  allow — read-only gh (forge uses these for daily planning, 17 entries):
    • Bash(gh pr list:*)              • Bash(cd * && gh pr list:*)
    • Bash(gh pr view:*)              • Bash(cd * && gh pr view:*)
    • Bash(gh pr status)              • Bash(cd * && gh pr status)
    • Bash(gh issue list:*)           • Bash(cd * && gh issue list:*)
    • Bash(gh issue view:*)           • Bash(cd * && gh issue view:*)
    • Bash(gh run list:*)             • Bash(cd * && gh run list:*)
    • Bash(gh run view:*)             • Bash(cd * && gh run view:*)
    • Bash(gh repo view:*)            • Bash(cd * && gh repo view:*)
    • Bash(gh search:*)
        cd-prefixed forms cover forge's `cd <repo> && gh ...` pattern.
        Excludes gh api / pr create / pr merge / issue create (mutating).

  allow — read-only tea / Forgejo CLI (mirrors gh, 18 entries):
    • Bash(tea pulls list:*)          • Bash(cd * && tea pulls list:*)
    • Bash(tea pulls ls:*)            • Bash(cd * && tea pulls ls:*)
    • Bash(tea pulls show:*)          • Bash(cd * && tea pulls show:*)
    • Bash(tea issues list:*)         • Bash(cd * && tea issues list:*)
    • Bash(tea issues ls:*)           • Bash(cd * && tea issues ls:*)
    • Bash(tea issues show:*)         • Bash(cd * && tea issues show:*)
    • Bash(tea repos list:*)          • Bash(cd * && tea repos list:*)
    • Bash(tea repos ls:*)            • Bash(cd * && tea repos ls:*)
    • Bash(tea repos show:*)          • Bash(cd * && tea repos show:*)
        Skip prompt-free if user has no Forgejo/Gitea remotes (entries
        match nothing harmful). For users on GitHub-only setups, harmless.

  deny (hard blocks for truly dangerous ops, 17 entries):
    • Bash(rm -rf /)                — wipe filesystem
    • Bash(rm -rf /*)               — wipe filesystem
    • Bash(rm -rf ~)                — wipe home
    • Bash(rm -rf ~/)               — wipe home
    • Bash(rm -rf $HOME)            — wipe home
    • Bash(rm -rf $HOME/)           — wipe home
    • Bash(sudo:*)                  — privilege escalation
    • Bash(su:*)                    — privilege escalation
    • Bash(doas:*)                  — privilege escalation
    • Bash(pkexec:*)                — privilege escalation (polkit)
    • Bash(osascript:*)             — macOS shell-script escalation
    • Bash(curl * | sh)             — remote code execution
    • Bash(curl * | bash)           — remote code execution
    • Bash(wget * | sh)             — remote code execution
    • Bash(wget * | bash)           — remote code execution
    • Bash(dd if=/dev/*)            — disk destruction
    • Bash(mkfs:*)                  — format disk

Nothing in the deny list will execute under any mode. Everything else
gets auto-approved with background safety checks. Changes take effect
in your next Claude Code session.

Note: "auto" mode is a documented Claude Code feature marked as research
preview. If it changes behavior in a future release, you can fall back
to `defaultMode: "default"` (standard prompting).
───────────────────────────────────────────────────────────────
```

### 5.2 Ask approval

Use AskUserQuestion:

```
Configure permissions in ~/.claude/settings.json? [Y/n]
```

Default: yes (they just set up the plugin; they want it to work).

### 5.3 If approved: write safely

Build the complete settings object in memory across steps 1–6; write to disk once at step 7. If any step fails, do not write partial state — restore the original file and report (per the validation invariant in 5.6).

1. Read `~/.claude/settings.json` (if missing, treat as `{}` in memory — defer any write until step 7)
2. Parse as JSON (in memory)
3. If `permissions` key doesn't exist, add it in memory: `{"permissions": {}}`
4. Set `permissions.defaultMode = "auto"` (overwrite if already set to something else — warn user)
5. Ensure `permissions.allow` is a list; add these 58 entries if not present (dedupe by exact string match).

   **Substitute `{NOTES_ROOT_ABS}` and `{CAIRN_HOME_ABS}` with the absolute values resolved in 5.0. Never write `~` into an entry.**

```
# Notes vault (5)
Read({NOTES_ROOT_ABS}/**)
Write({NOTES_ROOT_ABS}/**)
Edit({NOTES_ROOT_ABS}/**)
Glob({NOTES_ROOT_ABS}/**)
Grep({NOTES_ROOT_ABS}/**)

# Identity file (4)
Read({CAIRN_HOME_ABS}/**)
Write({CAIRN_HOME_ABS}/**)
Edit({CAIRN_HOME_ABS}/**)
Glob({CAIRN_HOME_ABS}/**)

# Project-local .notes symlink view (5)
Read(.notes/**)
Write(.notes/**)
Edit(.notes/**)
Glob(.notes/**)
Grep(.notes/**)

# Bash shapes the spokes use (9)
Bash(git rev-parse:*)
Bash(mkdir:*)
Bash(ln:*)
Bash(readlink:*)
Bash(rm .notes/**:*)
Bash(rm -r .notes/.agents/**:*)
Bash(echo:*)
Bash(date:*)
Bash(test:*)

# Read-only gh, bare + cd-prefixed (17)
Bash(gh pr list:*)
Bash(gh pr view:*)
Bash(gh pr status)
Bash(gh issue list:*)
Bash(gh issue view:*)
Bash(gh run list:*)
Bash(gh run view:*)
Bash(gh repo view:*)
Bash(gh search:*)
Bash(cd * && gh pr list:*)
Bash(cd * && gh pr view:*)
Bash(cd * && gh pr status)
Bash(cd * && gh issue list:*)
Bash(cd * && gh issue view:*)
Bash(cd * && gh run list:*)
Bash(cd * && gh run view:*)
Bash(cd * && gh repo view:*)

# Read-only tea / Forgejo CLI, bare + cd-prefixed (18)
Bash(tea pulls list:*)
Bash(tea pulls ls:*)
Bash(tea pulls show:*)
Bash(tea issues list:*)
Bash(tea issues ls:*)
Bash(tea issues show:*)
Bash(tea repos list:*)
Bash(tea repos ls:*)
Bash(tea repos show:*)
Bash(cd * && tea pulls list:*)
Bash(cd * && tea pulls ls:*)
Bash(cd * && tea pulls show:*)
Bash(cd * && tea issues list:*)
Bash(cd * && tea issues ls:*)
Bash(cd * && tea issues show:*)
Bash(cd * && tea repos list:*)
Bash(cd * && tea repos ls:*)
Bash(cd * && tea repos show:*)
```

6. Ensure `permissions.deny` is a list; add these 17 entries if not present (dedupe by exact string match, same as allow):

```
Bash(rm -rf /)
Bash(rm -rf /*)
Bash(rm -rf ~)
Bash(rm -rf ~/)
Bash(rm -rf $HOME)
Bash(rm -rf $HOME/)
Bash(sudo:*)
Bash(su:*)
Bash(doas:*)
Bash(pkexec:*)
Bash(osascript:*)
Bash(curl * | sh)
Bash(curl * | bash)
Bash(wget * | sh)
Bash(wget * | bash)
Bash(dd if=/dev/*)
Bash(mkfs:*)
```

Note: a fork-bomb entry like `Bash(:(){ :|: & };:)` is omitted intentionally — Claude Code's settings schema rejects empty parentheses inside the bash pattern, so it fails validation on write.

7. Write the updated JSON back, preserving all other existing settings (hooks, enabledPlugins, etc.). Use 2-space indentation.
8. Report the config:

```
Set defaultMode: "auto"
Added N new allow entries.
Added M new deny entries.

These take effect in your next session. To review or remove later:
  ~/.claude/settings.json  →  permissions
```

### 5.4 If declined: graceful acknowledgment

```
Skipped. You'll get permission prompts on first use of each path — you can
approve-and-remember at that point, or re-run /cairn-setup later.
```

Don't argue or re-prompt. Move on to Phase 6.

### 5.5 Idempotency

If the user re-runs `/cairn-setup` and all entries are already present:

```
Permissions already configured (all entries present). Nothing to add.
```

If some are present and some missing (rare, e.g., user deleted a few manually), add only the missing ones.

### 5.6 Safety invariants

- **Never replace** the `permissions.allow` array — always append.
- **Never replace** the `permissions.deny` array — always append. Never modify `permissions.ask` or any other permissions key.
- **Never modify** `hooks`, `enabledPlugins`, or any unrelated section.
- **Validate JSON** after write — if parse fails, restore the original and report.
- If `~/.claude/settings.json` doesn't exist, create it with only `{"permissions": {"defaultMode": "auto", "allow": [...], "deny": [...]}}` — nothing else (both lists populated on first create).

---

## Phase 6: Confirm & handoff

After writing:

```
cairn-notes is set up. Identity written to ~/.claude/cairn/identity.md.

Quick test: try `/capture this is my first cairn` — `/capture` will:
- Auto-detect the note type
- Route it to the right vault (project `.notes/` if you're in a repo, otherwise your personal vault)
- Write the file via scribe and show you the path + wikilink

Your personal vault at ~/notes/{{PERSONAL_VAULT}}/ will be auto-created the first time you capture there.

Questions or issues? See README.md or open an issue at github.com/SnowboardTechie/cairn-notes
```

---

## Edge cases

### No existing Claude Code setup

User is brand new. All discovery returns empty. Ask all 5 required questions with generic defaults. This is still fast (~2 minutes).

### Conflicting discovered values

Example: CLAUDE.md says "Bryan Thompson" but a memory file says "bryan". Show both:

```
Found two possible names:
- "Bryan Thompson" (from ~/.claude/CLAUDE.md)
- "bryan" (from ~/.claude/memory/user_profile.md)

Which should cairn-notes use?
```

Let user pick or type a third option.

### Re-run with existing identity

Show current identity, ask "which fields to update?" with a list. Only re-ask selected fields. Preserve the rest.

### `~/notes/` already exists with custom structure

If the user already has `~/notes/` with 3+ vault names, offer discovery:

```
Found existing vaults:
- ~/notes/work
- ~/notes/personal
- ~/notes/research

Which one should be your default personal vault?
(You can choose any, including creating a new one.)
```

Use their answer as the personal_vault default.

---

## Constraints

- **Never** overwrite `~/.claude/cairn/identity.md` without user confirmation
- **Never** write to locations outside `~/.claude/cairn/`
- **Always** validate that timezone is a valid IANA string before writing
- **Always** expand `~` to absolute paths in the file
- **Keep the conversation brief.** This is setup, not a thinking session.
