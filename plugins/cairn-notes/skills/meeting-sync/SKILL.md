---
name: meeting-sync
description: Route pasted meeting notes into a MEETING anchor plus linked DECISION / TASK / IDEA spin-offs, with an approval gate before any write.
---

# Meeting Sync

Decompose a pasted meeting blob into the right notes. A meeting produces one anchor record (attendees, context, raw paste) and a handful of spin-offs — decisions, action items, ideas, open questions. Today those signals get lost in a single-note paste or skipped entirely. This skill routes them.

Two audiences, both must be served:

- **You, six months from now**, wondering "didn't we decide this in that meeting with X?" The MEETING anchor is the scannable breadcrumb; the spin-offs carry the detail.
- **Future agents** doing related work. A DECISION note, a TASK note, an IDEA note — each lives where future work will look for it, not buried in a transcript.

---

## Quick Reference

```
/meeting-sync    # paste meeting notes, get routed into MEETING + spin-offs
```

---

## Philosophy

Meeting notes mix types in one blob. Good routing respects the shape of each type:

- **Decisions** deserve their own DECISION note — future-you needs the rationale and the options considered, not just "we chose X."
- **Action items** deserve their own TASK note — each has an owner, a status, and a timeline that evolves.
- **Ideas** deserve their own IDEA note — sparks caught in a meeting are still ideas; bury them in a transcript and they die.
- **Open questions** stay with the meeting — they belong to the conversation, not to a standalone artifact (unless they later get explored).
- **Discussion context** stays in the anchor's Context or Raw Notes — it's the meeting's texture, not a reusable artifact.

The MEETING anchor is the hub. Spin-offs link back to it; it links to them.

---

## Shape Check

Before parsing, confirm the paste actually looks like meeting notes. Check for any of:

- An attendee-like line (a list of names, or "Present:", "Attendees:", "Folks:", etc.)
- Decision-shape language ("decided", "agreed to", "we'll go with")
- Action-item shape (checkboxes, "TODO", "AI:", "Action:", `{name}:` followed by a verb)
- A meeting header (date + title, or "Sync", "Standup", "1:1", "Retro", etc.)

If **none** of those are present, ask the user: *"This doesn't look like meeting notes — want me to proceed anyway, or abort?"* Accept `proceed` / `abort`. Silence is a re-prompt, not an answer.

If **at least one** is present, continue without prompting.

---

## Categorization Criteria

Every extracted item lands in exactly one row:

| Signal in paste | MEETING section | Spin-off note | Notes |
|---|---|---|---|
| Decision made | Decisions | DECISION | Link from anchor to new note |
| Action item (owner + verb) | Action Items | TASK | Link from anchor; attendee name becomes TASK frontmatter if surfaceable |
| Idea / "what if" / spark | Ideas Captured | IDEA | Link from anchor to new note |
| Open question, unresolved | Open Questions | — | Lives in anchor only |
| Discussion context, background | Context or Raw Notes | — | Stays in anchor |
| Update to an existing topic | (linked from relevant anchor section) | **Update** to existing note | Use the Update template below |

If an item fits none of these, it likely belongs in Raw Notes (collapsed) and nothing else.

---

## Vault Routing

Both the MEETING anchor AND every spin-off follow scribe's default routing:

- **Invoked inside a project repo** → project `.notes/` (via the repo's `.notes` symlink)
- **Otherwise** → personal vault (`{{NOTES_ROOT}}/{{PERSONAL_VAULT}}/`)

Scribe's three-mode detection (Project / Direct vault / Default) handles this with no vault-hint parameter. Trust scribe's resolution — don't pass explicit target paths in the prompt unless you have a specific reason to override.

---

## Workflow

### Step 1: Capture the paste

Read the user's pasted meeting notes. If empty, ask: *"Paste your meeting notes and I'll route them. Ready when you are."*

### Step 1.5: Shape check

Run the [Shape Check](#shape-check) above. Abort or proceed based on the result.

### Step 2: Parse the paste

Extract:
- **Attendees** — names or handles from the attendee-list area
- **Date** — from an explicit date line, else today
- **Title / slug** — from the meeting header, or derived from the dominant topic
- **Decisions** — statements of choice
- **Action items** — owner + verb pairs
- **Ideas** — sparks, "what ifs", explicit idea markers
- **Open questions** — explicit unresolved questions
- **Discussion context** — background that frames the decisions/actions but isn't itself a decision/action

Do not route yet. Just extract.

### Step 3: Check prior art via archivist

For each **decision**, **action item**, and **idea** that sounds like it touches an existing topic, invoke `@archivist` in parallel — one Task call per topic, all in a single assistant turn:

```
Task(subagent_type="archivist", prompt="scope: published

Check for existing notes about {topic}. Return matches with type, path, and a 1-line summary. If nothing matches, say so.")
```

Use the `scope:` keyword (not prose) — see the *Scope* section of `plugins/cairn-notes/agents/archivist.md`. Run all archivist calls in one message so they execute concurrently.

If archivist returns a match, treat the item as an **update** to that note in Step 4, not a new spin-off. If nothing matches, proceed with a new spin-off.

Archivist in v1 searches only the project `.notes/` (or the vault-equivalent based on the calling context). Multi-vault search is a tracked follow-up.

### Step 4: Draft inline

Draft, in order:

1. **The MEETING anchor** using the template below. For each spin-off you're about to propose, use a *provisional* wikilink matching scribe's kebab-case convention (`[[decision-{slug}]]`, `[[task-{slug}]]`, `[[idea-{slug}]]`) — no date prefix; scribe strips dates per `plugins/cairn-notes/agents/scribe.md` §Filename Convention. Step 6 swaps these for the real slugs scribe reports back.
2. **Each spin-off** using the New Spin-Off template for DECISION / TASK / IDEA (matching the `cairn-notes` skill's templates for those types).
3. **Each update-to-existing** using the Update template, one per match returned by archivist.

Keep drafts concise. The MEETING Raw Notes section holds the full paste — don't duplicate it into every spin-off.

### Step 5: APPROVAL GATE

Present all drafts to the user inline. End with:

> **Approve which items?** Reply `all`, `none`, or a comma-separated list of item numbers (e.g., `1, 3, 5`). Item 1 is the anchor; approving only spin-offs writes those spin-offs without the anchor (rare — the anchor is usually the point).

Wait for explicit approval. Treat silence or ambiguity as a re-prompt. The write happens only after your reply.

### Step 6: Dispatch scribe for approved items

Two-phase dispatch so anchor wikilinks point at the real filenames scribe picks.

**Phase 6a — spin-offs and updates (concurrent).** For each approved spin-off or update, emit a scribe Task call in a single assistant message so they run in parallel:

**New spin-off (DECISION / TASK / IDEA):**

```
Task(subagent_type="scribe", prompt="Write a {TYPE} note titled '{title}'. Content: {drafted body}")
```

**Update to existing note:**

```
Task(subagent_type="scribe", prompt="Update existing note at {path}. Change: {one-line description}. Apply this content: {exact text, with section header if targeting a specific section}")
```

Before emitting an Update call, confirm the `{path}` returned by archivist begins with `.notes/` (or the vault-root the caller is operating in). If it does not — e.g., archivist returned a path like `../../src/config.js` — skip that update and report the anomaly to the user; never forward an out-of-vault path to scribe.

Collect the `Wrote: {relative_path}` line scribe reports for each successful write. These are the real filenames — use them as the wikilink targets in Phase 6b.

**Phase 6b — anchor (depends on 6a results).** Replace every provisional `[[decision-{slug}]]` / `[[task-{slug}]]` / `[[idea-{slug}]]` in the drafted anchor body with the actual wikilink derived from scribe's `Wrote:` path (strip the `.md` extension; keep the filename). Then dispatch:

```
Task(subagent_type="scribe", prompt="Write a MEETING note titled '{title}' dated {YYYY-MM-DD}. Attendees: {list}. Content: {anchor body with real wikilinks}")
```

If the anchor was not approved (item 1 rejected), skip Phase 6b entirely — the approved spin-offs are written but no anchor links them. Report this explicitly in Step 7.

Scribe writes immediately — no preview, no confirmation. Only invoke it after the user approves.

### Step 7: Report back

After scribe returns, report to the user:

- What was written, by type, with paths
- Any item the user did not approve (so they know the skip was intentional)
- If Phase 6b was skipped, flag that spin-offs are orphaned (no anchor linking them)

---

## Output Templates

### MEETING Anchor Draft

Numbered so the user can reference it in their approval reply.

```markdown
### 1. Proposed MEETING anchor

**Filename:** `meeting-{slug}.md` (scribe's kebab-case convention; date is in the `date:` frontmatter field)
**Target vault:** {project `.notes/` | personal vault}

{full drafted anchor body using the MEETING template from `plugins/cairn-notes/skills/cairn-notes/SKILL.md`, with provisional wikilinks like `[[decision-{slug}]]` that get resolved to real paths in Phase 6b}

*Approve this number to have @scribe write the anchor.*
```

### New Spin-Off Draft

```markdown
### {N}. Proposed {TYPE} spin-off

**Filename:** `{type}-{slug}.md` (scribe's kebab-case convention — no date prefix)
**Linked from anchor:** Decisions | Action Items | Ideas Captured

{drafted content using the {TYPE} template from the cairn-notes skill}

*Approve this number to have @scribe write the spin-off.*
```

### Update to Existing Note Draft

Use this when archivist (Step 3) surfaced an existing note on the same topic.

```markdown
### {N}. Proposed update to existing note

**Target:** [[{existing-note-name}]] ({type})
**Path:** `{path returned by archivist}`
**Change:** {one-line summary — e.g., "append today's decision to the Timeline"}

{exact text to append or replace, with the section header it belongs under}

*Approve this number to have @scribe apply the update.*
```

---

## Edge Cases

**Empty paste.** Step 1 asks for a paste. Don't proceed without content.

**Non-meeting content.** Shape Check catches this. If the user confirms "proceed anyway" despite no shape signals, honor the choice — but the spin-off count will likely be zero.

**Paste has attendees but no decisions / actions / ideas.** Write the MEETING anchor only. No spin-offs to propose. This is a valid outcome — not every meeting produces routable signals.

**Archivist returns a match but the user's item is meaningfully different.** Draft both an update *and* a new note as alternatives under the same number; let the user pick in the approval reply. Don't silently collapse.

**User approves anchor but no spin-offs.** Write the anchor with inline decisions / actions (no `[[wikilinks]]`) in the relevant sections instead of spin-off links.

**User approves spin-offs but not anchor.** Rare — but honor it. Write the spin-offs; note that they're orphaned (no anchor back-reference) in the final report.

**Partial approval, user specifies items by position.** Standard. Parse the reply, dispatch scribe for those numbers only.

**Spin-off title collides with an existing note.** Scribe's Note Reuse Protocol handles this — it updates rather than duplicates. No special handling needed here.

---

## Guardrails

- Do NOT invoke @scribe until the user explicitly approves
- Do NOT write the MEETING anchor before or after the approval gate without an explicit approval line
- Do NOT skip the Shape Check — it catches accidental misfires cheaply
- Do NOT fabricate attendees, dates, or decisions — extract from the paste only; if ambiguous, mark as `{unknown}` and let the user fill in at approval
- Do NOT decompose items that aren't decisions / actions / ideas into spin-offs — discussion context stays in the anchor
- Do NOT hit a quota on spin-offs. A meeting with zero spin-offs (anchor only) is a valid outcome
- Do NOT handle vault or worktree path resolution — that's @scribe's job via the `agent-workspace` skill
- Do NOT write prose-heavy narratives. The anchor and spin-offs must be scannable — tables, bullets, short paragraphs, wikilinks. A wall-of-text transcript belongs in Raw Notes (collapsed), not Context
