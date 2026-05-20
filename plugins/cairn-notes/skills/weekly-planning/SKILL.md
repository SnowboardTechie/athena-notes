---
name: weekly-planning
description: Guided weekly planning session for ADHD - Q&A flow that writes a weekly plan to the personal vault. Triggers on "let's plan the week", "weekly planning", "plan my week", or `/weekly-planning`.
---

# Weekly Planning — Guided Session

A structured Q&A that walks the user through their weekly planning. Uses the VOMIT backbone (Vent → Obligations → Milestones → Investments → Tethers, adapted as Vent → Last Week → Obligations → Rocks → Energy → Today → Note → Whiteboard). Outputs a weekly-plan note in the personal vault.

Opinionated flow for ADHD brains: mandatory vent, hard cap at 3 rocks, permission-to-drop-rocks framing, whiteboard-friendly summary. If you want a generic weekly review, fork this — the phases are load-bearing, not incidental.

---

## When to Use

- Monday morning planning
- User says "let's plan the week", "weekly planning", "plan my week"
- `/weekly-planning` command
- `workday-planning` directs here on Mondays when the user wants depth beyond the week-prep overlay

## Quick Reference

```
/weekly-planning    # start a new weekly planning session
```

---

## Config

Reads two files; neither is required — both have sensible defaults.

### `~/.claude/cairn/identity.md` (vault root + personal vault)

```yaml
notes_root: ~/notes            # default: ~/notes
personal_vault: second-brain   # default: second-brain
```

Populated by `/cairn-setup`. If the file is missing, fall back to the defaults above — don't block planning on a missing identity.

### `~/.claude/cairn/planning-sources.md` (output folder)

This is the same config file `workday-planning` uses. Weekly-planning adds a nested `weekly_planning:` section alongside the existing top-level `output_folder` (which belongs to workday-planning):

```yaml
---
output_folder: Daily              # daily plans — workday-planning's key (ignored here)
weekly_planning:
  output_folder: Journal          # weekly plans — weekly-planning (default: Journal)
# ...other workday-planning keys (projects, etc.) may coexist here
---
```

- If the file is missing, use default `Journal`.
- If the file exists but has no `weekly_planning:` section, use default `Journal`.
- Do not bootstrap interactively — just use the default. If the user wants to customize, they edit the file (same pattern as workday-planning's top-level `output_folder`).
- **Validate the value.** Before interpolating into a filesystem path, reject any `output_folder` that contains `..` or starts with `/` (absolute paths). On rejection, warn once and fall back to default `Journal`. Prevents path traversal via a hand-edited or accidentally clobbered config.

### Resolved output path

```
{notes_root}/{personal_vault}/{weekly_planning.output_folder}/{YYYY-MM-DD}-weekly-plan.md
```

Typical: `~/notes/second-brain/Journal/2026-04-27-weekly-plan.md`.

Create the output directory silently if missing. Don't ask.

---

## Session Flow

Run as an interactive Q&A. Each phase maps to a section of the output note. Conversational — this isn't a form, it's a thinking session. Use `AskUserQuestion` where structured options help (Phase 2's "how did last week go?"); otherwise ask open-ended.

### Phase 0: Setup

Before asking anything:

1. Resolve `notes_root` + `personal_vault` from `identity.md`. Resolve `weekly_planning.output_folder` from `planning-sources.md` (default `Journal`). Compute the output path.
2. Check for last week's planning note: `Glob` `{notes_root}/{personal_vault}/{weekly_planning.output_folder}/*-weekly-plan.md`, take the newest. If found, read it — especially the rocks and end-of-week sections. Note any incomplete rocks or carry-forward items.
3. **Invoke scout** for developer-forge obligations (unless the user said "skip github" / "skip forge" / "no forgejo" earlier in the session):

   ```
   Task(subagent_type="scout", prompt="Fetch forge activity for weekly planning (cwd={resolved personal vault path})")
   ```

   Resolve the `cwd` value yourself — typically the personal vault path from Step 1, since weekly planning usually happens from the vault (not a code repo). Scout defaults to GitHub. Hold scout's summary for Phase 3. If scout returns `{forge}_available: false`, continue without — don't block the session.

### Phase 1: Vent (Clear the Noise)

> The VOMIT system starts with Vent. ADHD brains can't plan when they're full of noise.

Ask:

```
Before we plan — what's on your mind right now? Any stress, frustration, or
mental noise you want to dump out first? This doesn't need to be organized.
Just get it out.
```

- Let them vent freely.
- Don't try to solve anything here.
- Acknowledge what they shared, then transition: "Good, that's out of your head now. Let's look at last week."

### Phase 2: Last Week Review

> If a previous weekly note exists, reference specific rocks from it.

Ask via `AskUserQuestion` (options based on last week's rocks). If no previous note, ask open-ended.

```
question: "How did last week go?"
header: "Last week"
options:
  - label: "Crushed it"        description: "Got most/all rocks done"
  - label: "Mixed bag"         description: "Some progress, some dropped"
  - label: "Rough week"        description: "Not much landed"
  - label: "First week"        description: "No previous plan to review"
```

Then follow up per rock:

```
What happened with [rock]? Done, in progress, or dropped?
```

Collect:
- **Wins** — what got done (celebrate briefly — dopamine matters).
- **Dropped** — what didn't happen (no judgment, just note it).
- **Carry forward** — anything that should become a rock this week.

### Phase 3: Obligations (VOMIT - O)

> Surface what actually needs doing. "Will it make the boat go faster?"

If scout returned a summary in Phase 0, present it first before asking the open question:

```
Before you tell me what's on your plate — here's what {github|forgejo} is
showing right now:

{scout summary verbatim}

Anything here you want to pull into this week's obligations?
```

Let the user opt items in or dismiss the whole block. Then ask:

```
What other obligations or commitments do you have this week? Work deadlines,
appointments, things you promised someone — anything with a real external
deadline or expectation.
```

This grounds the rocks in reality. Some rocks might be obligations, some might be personal goals.

### Phase 4: Pick 3 Rocks

> This is the core decision. Constrain to exactly 3.

Present what you've gathered:
- Carry-forward items from last week (Phase 2).
- Obligations surfaced in Phase 3.

Then ask:

```
question: "Based on everything above — what are your 3 rocks for this week?
These should be the 3 things that, if you did nothing else, you'd feel good
about the week."
header: "3 Rocks"
```

For each rock, follow up:

```
Why does [rock] matter this week specifically? (One sentence is fine.)
```

**If they list more than 3:** Push back gently. "You listed [N]. The constraint is the feature — which 3 matter most? The rest can wait."

**If they list fewer than 3:** That's fine. 2 rocks is a real week. 1 rock with full focus is better than 3 with scattered attention.

**If they say they don't know what their rocks should be:** Ask inline: "What projects are you juggling? I can help you pick from there." Then pick from what they list.

### Phase 5: Energy Routing

Ask:

```
Let's set up your "when stuck" options. For each energy level, what's one
thing you could do?

⚡ High energy (focused, sharp)   → what task needs your best brain?
🔧 Medium energy (functional)    → what maintenance or routine task?
📖 Low energy (tired, scattered) → what passive or easy thing could you do?
```

These don't need to be rocks. They can be anything — chores, reading, organizing, walks. The point is a pre-decided answer for "I don't know what to do right now."

### Phase 6: Today's One Thing

Ask:

```
What's the ONE thing you're going to do today that moves one of your rocks
forward? Just one.
```

### Phase 7: Generate the Note

Using all collected answers, write the weekly plan to the resolved output path. Create the parent directory if missing.

Structure (embedded inline — no external template file required):

~~~markdown
---
date: {YYYY-MM-DD}
type: weekly-plan
week_of: {Monday of this week, YYYY-MM-DD}
---

# Weekly Plan — Week of {Monday, Month D, YYYY}

## Vent

{user's Phase 1 dump, lightly formatted; omit the whole section if they skipped}

## Last Week

### Wins
- {bullet}

### Dropped
- {bullet}

### Carry forward
- {bullet}

## Obligations

{Phase 3 obligations, bulleted. If scout contributed, mark those items with a trailing `(via {github|forgejo})`.}

## This Week's 3 Rocks

1. **{rock 1}** — {why it matters}
2. **{rock 2}** — {why it matters}
3. **{rock 3}** — {why it matters}

## Energy Routing

- ⚡ High → {high energy task}
- 🔧 Medium → {medium energy task}
- 📖 Low → {low energy task}

## Today

→ {today's one thing}

## Whiteboard

```
THIS WEEK'S 3 ROCKS
━━━━━━━━━━━━━━━━━━━
1. {rock 1}
2. {rock 2}
3. {rock 3}

TODAY → {today's one thing}

WHEN STUCK:
⚡ High   → {high energy task}
🔧 Med    → {medium energy task}
📖 Low    → {low energy task}
```
~~~

Add wikilinks (`[[Project Name]]`, etc.) where the user referenced named projects or notes — follow the `obsidian` skill's wikilink conventions. Don't force wikilinks where the user didn't name something specific.

### Phase 8: Whiteboard Summary

After saving, print the saved file path, then present the whiteboard block as a standalone message the user can copy to their physical board:

```
Saved: {resolved output path}

Here's what goes on your whiteboard this week:

THIS WEEK'S 3 ROCKS
━━━━━━━━━━━━━━━━━━━
1. {rock 1}
2. {rock 2}
3. {rock 3}

TODAY → {today's one thing}

WHEN STUCK:
⚡ High   → {high energy task}
🔧 Med    → {medium energy task}
📖 Low    → {low energy task}
```

---

## Tone Guidelines

- **Warm but direct.** Thinking partner, not therapist or drill sergeant.
- **Keep it moving.** Target 5–10 minutes end-to-end. Don't over-discuss.

---

## Edge Cases

**User is having a really rough day:**
Don't force the full flow. Ask: "Do you want to do the full planning session, or just pick one rock and call it a week?" One rock is valid.

**User wants to skip the vent:**
Let them. It's optional. Jump to Phase 2.

**No previous weekly note exists:**
Skip Phase 2's rock review. Ask open-ended: "How was last week in general?"

**User is mid-week:**
Adjust language — "rest of the week" instead of "this week." Still pick 3 rocks (or fewer).

**User says "skip github" / "skip forge" / "no forgejo" (before or during Phase 0):**
Don't invoke scout. Proceed without a forge-activity section in Phase 3.

**Scout returns `{forge}_available: false`:**
The CLI (`gh` or `tea`) is missing or not authed. Silently continue without the forge-activity block in Phase 3. Don't prompt the user to install anything.

**Output file already exists for today:**
Ask: overwrite, or append a `-2` suffix? No silent merge.

**`planning-sources.md` has a `weekly_planning:` key but it's malformed (not a mapping):**
Warn once and fall back to default `Journal`. Don't halt — user can fix the file and rerun.

**User ran `/plan-workday --edit-sources` and the `weekly_planning:` key is missing from the post-bootstrap file:**
Workday-planning's bootstrap is supposed to preserve this key (see its Bootstrap Flow Step 0). If it didn't, flag the bug — a missing key after bootstrap means Step 0 regressed. In the interim this skill falls back to default `Journal`.

---

## Dependencies

- `obsidian` skill — vault path conventions and wikilink syntax.
- `cairn-notes` skill — note type patterns (this is a `weekly-plan` type note; follows the same frontmatter/linking conventions).
- `scout` agent — optional forge-activity fetch for Phase 0.

---

## Guardrails

- Do NOT skip the vent phase unprompted.
- Do NOT allow more than 3 rocks without pushback.
- Do NOT make the session feel like a performance review — it's planning, not grading.
- Do NOT add rocks the user didn't choose — this is their plan, not yours.
- Do NOT hardcode vault paths — always resolve from `identity.md` with fallback defaults.
- ALWAYS present the whiteboard summary at the end — it's the bridge between digital and physical.
