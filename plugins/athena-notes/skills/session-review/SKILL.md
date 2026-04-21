---
name: session-review
description: Review conversation sessions for project-specific learnings to document in AGENTS.md and .notes/
---

# Session Review

Surface learnings worth preserving. Two audiences, both must be served:

- **You, six months from now**, skimming in Obsidian on a Saturday. A note that wouldn't earn a second look then shouldn't be written now.
- **Future agents** deciding something similar. A note that doesn't change a concrete future decision is noise.

If a candidate serves neither, it doesn't become a note. Zero items is a normal outcome — most sessions execute rather than discover. Signal is rare by definition; quota-hitting is the failure mode.

---

## Quick Reference

```
/session-review    # review this session for learnings to capture
```

---

## Philosophy

Good sessions produce knowledge that shouldn't live only in your head. This skill finds that knowledge and routes it to the right place. The goal is signal, not completeness — a session with one sharp insight is better documented than one with ten mediocre ones.

**What's not signal:**

- **Post-mortems of single incidents.** If the takeaway is "we should have followed the existing rule," the existing rule is already the signal; the anecdote doesn't add it.
- **Reinforcement of existing AGENTS.md rules.** If the rule is already documented, a new note about violating or rediscovering it is noise.
- **General engineering hygiene.** Git quirks, shell gotchas, language patterns, editor tricks — a future agent will pick these up from tool docs and context. Not project-specific, not signal.
- **Aspirational "we should" notes** where no concrete convention was actually agreed. Intentions aren't conventions.
- **Activity logs.** "We did X, then Y, then Z" is a log. Signal is the *rule* or *decision* extracted from the activity, not the activity itself.

---

## Signal Test

Before categorizing or drafting, every candidate must pass **all four** questions. Any "no" drops the candidate.

1. **Novel.** Is the rule, decision, or pattern already captured in AGENTS.md or an existing `.notes/` note? If so, the existing record *is* the signal.
2. **Project-specific.** Is this specific to Athena Notes (agents, skills, vaults, identity, hub-spoke, this repo's layout)? General engineering knowledge fails.
3. **Future-actionable.** Will a concrete decision — in a future chat or by your future self — change because this note exists? If removing the note wouldn't change any future outcome, it's a log.
4. **Readable in six months.** Would the note earn a second look in Obsidian on a Saturday? Scannable (table, bullets, wikilinks, short paragraphs) — or a wall of prose to scroll past? If the latter: compress or drop.

Zero survivors is fine. Better to capture nothing than to grow an archive you never revisit.

---

## Categorization Criteria

| Learning Type | Destination | Target Section | Example |
|---------------|-------------|----------------|---------|
| Convention discovered | AGENTS.md | CONVENTIONS | "Always use expandtab in Lua files" |
| Gotcha / anti-pattern | AGENTS.md | ANTI-PATTERNS | "Never stow ~/.gnupg directly" |
| Location knowledge | AGENTS.md | WHERE TO LOOK | "Health endpoint: src/api/health.ts" |
| Architectural decision | .notes/ | DECISION type | "Chose JWT over sessions because..." |
| Deep exploration | .notes/ | EXPLORATION type | "Investigated caching strategies..." |
| Key insight | .notes/ | SESSION type | "Realized the auth flow requires..." |

---

## Workflow

### Step 1: Scan the conversation

Read back through the session. Look for moments where something was discovered, decided, or clarified. Ignore routine task execution. Flag candidates — no quota. Most sessions produce zero to two.

### Step 1.5: Apply the Signal Test

Run each candidate against the four questions above. Drop any that don't pass all four. This is the filter that does the real work; downstream steps only handle survivors.

### Step 2: Read existing context

Before drafting anything, check for prior art in **both** places so you don't propose duplicates or orphan the existing knowledge:

1. **AGENTS.md** — read it (if it exists). Understand the current sections. Skip any learning already captured there.
2. **`.notes/`** — for each surviving candidate that could plausibly land in `.notes/` (architectural decisions, explorations, key insights — the bottom three rows of the categorization table below), invoke `@archivist` to check whether a note on this topic already exists. If a candidate is unambiguously an AGENTS.md row (convention, anti-pattern, where-to-look), skip the archivist call — `.notes/` isn't its destination.

   ```
   Task(subagent_type="archivist", prompt="Check .notes/ for existing notes about {topic}. Scope: published notes, not .agents/ working files. Return matches with type, path, and a 1-line summary. If nothing matches, say so.")
   ```

   If archivist returns a match, treat the candidate as an **update** to that note, not a new one. Draft it using the Update template below.

Run archivist lookups in parallel — emit all Task calls in one assistant message so they run concurrently, not one per turn. This step should add seconds, not minutes.

### Step 3: Categorize

Map each candidate to a row in the table above. If it doesn't fit any row, it probably isn't worth capturing.

### Step 4: Draft inline

Write out proposed content for each item using the templates below. Keep drafts concise — one table row for AGENTS.md, a filled template for a new `.notes/` note, or a targeted patch for an update.

### Step 5: APPROVAL GATE

Present all drafts to the user and stop. Do not proceed until you receive explicit approval. The user may approve all, some, or none.

### Step 6: Write or update approved .notes/ items

For each approved `.notes/` item, invoke `@scribe`. Use the shape that matches the draft:

**New note:**

```
Task(subagent_type="scribe", prompt="Write a {TYPE} note titled '{title}'. Content: {draft content}")
```

**Update to an existing note:**

```
Task(subagent_type="scribe", prompt="Update existing note at {path}. Change: {one-line description}. Apply this content: {exact text, with section header if targeting a specific section}")
```

Scribe writes (or edits) immediately on invocation — no preview, no confirmation. Only call it after the user approves.

### Step 7: Present AGENTS.md copy-paste

For each approved AGENTS.md item, show the final markdown block. Never write to AGENTS.md directly. The user manages that file.

---

## Output Templates

### AGENTS.md Draft

```markdown
### Proposed AGENTS.md Addition

**Section:** {CONVENTIONS | ANTI-PATTERNS | WHERE TO LOOK | NOTES}

```markdown
| {context} | {guidance} |
```

*Copy the above into your AGENTS.md*
```

### .notes/ Draft (new note)

```markdown
### Proposed .notes/ Entry

**Type:** {DECISION | EXPLORATION | SESSION}
**Filename:** `{YYYY-MM-DD}-{type}-{slug}.md`

{Draft content using the athena-notes template for that type}

*Approve to have @scribe write this note*
```

### .notes/ Draft (update to existing note)

Use this variant when archivist (Step 2) surfaced an existing note on the same topic.

```markdown
### Proposed .notes/ Update

**Target:** [[{existing-note-name}]] ({type})
**Path:** `{path returned by archivist}`
**Change:** {one-line summary — e.g., "add insight to Open Questions", "append new option to alternatives considered"}

{exact text to append or replace, with the section header it belongs under}

*Approve to have @scribe apply this update*
```

---

## Edge Cases

**No survivors (common):** Most sessions execute rather than discover. Report `No signal — routine execution` and stop. This isn't failure; it's the expected outcome.

**No AGENTS.md in project:** Skip the AGENTS.md section entirely. Still offer `.notes/` drafts for survivors.

**Duplicate learning:** If the insight already exists in AGENTS.md, the Signal Test already dropped it. If an existing `.notes/` note on the same topic is found in Step 2, propose an **update** to that note instead of a new one — never silently create a second note on the same subject.

**Very long session:** Length doesn't entitle a session to more notes. Apply the Signal Test and see what survives. A six-hour session with zero survivors is a valid outcome.

---

## Guardrails

- Do NOT invoke @scribe until the user explicitly approves the draft
- Do NOT write to AGENTS.md directly — always present as copy-paste markdown
- Do NOT fabricate learnings — every item must trace to a specific moment in the conversation
- Do NOT create new AGENTS.md sections — fit content into existing structure
- Do NOT handle worktree path resolution — that's @scribe's job via the agent-workspace skill
- Do NOT write prose-heavy narratives. Notes must be scannable in Obsidian at a glance — tables, bullets, wikilinks to related notes, short paragraphs. A 300-word reflective essay is the failure mode, not the goal.
- Do NOT hit a quota. If only one candidate survives the Signal Test, propose one. If none survive, propose none. Never pad.
