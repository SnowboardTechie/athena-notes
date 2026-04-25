---
name: session-review
description: Review conversation sessions for project-specific learnings (AGENTS.md / .notes/), cross-project user-collaboration preferences (harness memory), and resolved tracked items (today's daily plan)
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

Before categorizing or drafting, every candidate must pass the questions that apply to its route — vault-route candidates take all four, memory-route candidates take the subset noted in Step 1.5. Any "no" on a question that applies drops the candidate.

**Exemption:** Daily-plan status updates from Step 1.6 (tracked-item resolutions) skip this filter — they're state changes, not durable insights, and the questions are tuned for knowledge. A session with zero insight-signal can still close a planned loop.

1. **Novel.** Is the rule, decision, or pattern already captured in AGENTS.md or an existing `.notes/` note? If so, the existing record *is* the signal.
2. **Durable & scoped.** The candidate routes to one of two destinations:

   - **Vault** (→ AGENTS.md / `.notes/`) — project-specific to Athena Notes: agents, skills, vaults, identity, hub-spoke, this repo's layout.
   - **Harness memory** — cross-project user-collaboration preference (how this user thinks, anchors, decides), project motivation / stakeholder context, or external-system pointer.

   A transient session vibe isn't durable; a general engineering truism isn't scoped. Neither qualifies.
3. **Future-actionable.** Will a concrete decision — in a future chat or by your future self — change because this note exists? If removing the note wouldn't change any future outcome, it's a log.
4. **Readable in six months.** Would the captured item earn a second look — vault notes in Obsidian on a Saturday, memory records in a future session window? Scannable (table, bullets, short paragraphs; wikilinks for vault notes only) — or a wall of prose to scroll past? If the latter: compress or drop.

Zero survivors is fine. Better to capture nothing than to grow an archive you never revisit.

---

## Categorization Criteria

**Vault routes** (project-specific findings; written by `@scribe` or direct edits to AGENTS.md / today's daily plan):

| Learning Type | Destination | Target Section | Example |
|---------------|-------------|----------------|---------|
| Convention discovered | AGENTS.md | CONVENTIONS | "Always use expandtab in Lua files" |
| Gotcha / anti-pattern | AGENTS.md | ANTI-PATTERNS | "Never stow ~/.gnupg directly" |
| Location knowledge | AGENTS.md | WHERE TO LOOK | "Health endpoint: src/api/health.ts" |
| Architectural decision | .notes/ | DECISION type | "Chose JWT over sessions because..." |
| Deep exploration | .notes/ | EXPLORATION type | "Investigated caching strategies..." |
| Key insight | .notes/ | SESSION type | "Realized the auth flow requires..." |
| Tracked-item resolution | today's daily plan | matching line | "`#734 → triaged out-of-scope`" |

**Memory routes** (cross-project collaboration signal; routed to the harness memory system — Claude Code auto-memory or equivalent. If your harness has no memory system, present the finding to the user as a candidate worth recording wherever they keep cross-project preferences):

| Learning Type | Destination | Target | Example |
|---------------|-------------|--------|---------|
| User-collaboration preference | Harness memory | feedback / user record | "Leads with standards-alignment, not as a footnote" |
| Project motivation / stakeholder context | Harness memory | project record | "Auth migration is compliance-driven, not tech-debt cleanup" |
| External-system pointer | Harness memory | reference record | "Pipeline bugs live in Linear project INGEST" |

> **Scoping note.** Pointers that name internal infrastructure (private URLs, internal IDs, internal tooling) are project-scoped — write them to `.notes/` on the originating project, not to cross-project memory.

---

## Workflow

### Step 1: Scan the conversation

Read back through the session with **two lenses**:

- **Technical lens.** Moments where something about the code, architecture, or project state was discovered, decided, or clarified.
- **Collaboration lens.** Moments where the user redirected your framing, elevated a "minor" suggestion to a main issue, repeatedly anchored to a standard or principle, or endorsed an unusual approach without pushback. Signal about *how the user thinks* — routes to the harness memory system, not AGENTS.md / `.notes/`.

A session can have signal in one lens, both, or neither. Ignore routine task execution. Flag candidates — no quota. Most sessions produce zero to two.

### Step 1.5: Apply the Signal Test

Run each candidate against the four questions above. Drop any that don't pass.

- **Vault-route candidates** (AGENTS.md / `.notes/` / daily plan): all four questions must pass.
- **Memory-route candidates** (harness memory): Q2 (durable & scoped), Q3 (future-actionable), and Q4 (readable in six months) all apply. Q1 (novel-in-vault) doesn't — memory is a separate index from the vault. A preference that wouldn't change any future agent decision still fails Q3.

Routing is by destination row, not by which lens flagged the candidate — a technical-lens finding can land on memory-routes if it fits a project-motivation or external-system-pointer row.

This is the filter that does the real work; downstream steps only handle survivors.

### Step 1.6: Scan today's daily plan for resolved items

A session often closes a loop that was tracked on today's daily plan (e.g., `[P3 afternoon] Triage #646 / #734 / #731`). Step 1's lenses target knowledge moments (technical discoveries, collaboration patterns); the Signal Test is insight-tuned. Tracked-item resolutions are state changes, so they slip through both. This step catches them.

1. **Resolve today's plan path** (same convention as `workday-planning` Phase 0):
   - Read `~/.claude/athena/identity.md` → `notes_root` (default `~/notes`), `personal_vault` (default `second-brain`), `TZ` (IANA).
   - Read `~/.claude/athena/planning-sources.md` frontmatter → `output_folder` (default `Daily`).
   - TZ validation: must match `^(UTC|[A-Za-z][A-Za-z0-9_+-]*/[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z][A-Za-z0-9_+-]*)?)$`. On mismatch, warn once and fall back to system TZ. If the validated-TZ `date` invocation exits non-zero (shape-valid but the zone doesn't exist on this system, e.g. `America/Fakeville`), re-run without `TZ` and emit the same fallback warning.
   - Compute today's date in that zone: `TZ="{{TIMEZONE}}" date +%Y-%m-%d` (or plain `date +%Y-%m-%d` on fallback).
   - Path: `{notes_root}/{personal_vault}/{output_folder}/{YYYY-MM-DD}-daily-plan.md`. If `output_folder` is `.`, the path is `{notes_root}/{personal_vault}/{YYYY-MM-DD}-daily-plan.md` (vault root).
2. **If the file doesn't exist:** silently skip this step. No prompt, no error. Not every session follows a planned day.
3. **If it exists:** read it and scan for tracked items — any list/bullet line referencing an issue/PR (`#N`, `owner/repo#N`), a named task, or a time-block item the session clearly addressed. Ignore section headings and frontmatter / metadata lines.
4. **Match against the conversation.** For each tracked item, was it resolved, triaged, decided, or invalidated in this session? Look for concrete evidence (a decision, a comment posted, a pivot). If the session didn't touch the item, skip it.
5. **Draft in-place edits only.** Use whatever convention the plan already uses (checkbox, strike-through, nested bullet) or append a short `→ resolved: {one-line outcome}` suffix. Do not rewrite the plan, do not add sections, do not reorder items. If a user pivot invalidated a sibling detail on the plan, propose that edit too.
6. **Zero matches is fine** — equivalent to "no signal" for the knowledge path.

Outputs from this step bypass Steps 1.5, 2, and 3 — they don't need the Signal Test (state, not insight), prior-art checks (in-place edits, not new knowledge), or categorization (the table already routes them). They go straight to Step 4, drafted with the Daily-plan update template, and then to the Step 5 approval gate.

### Step 2: Read existing context

Before drafting anything, check for prior art so you don't propose duplicates or orphan the existing knowledge:

1. **AGENTS.md** — read it (if it exists). Understand the current sections. Skip any learning already captured there.
2. **`.notes/`** — for each surviving candidate that could plausibly land in `.notes/` (architectural decisions, explorations, key insights — the corresponding rows in the vault-routes table above), invoke `@archivist` to check whether a note on this topic already exists. If a candidate is unambiguously an AGENTS.md row (convention, anti-pattern, where-to-look), skip the archivist call — `.notes/` isn't its destination.

   ```
   Task(subagent_type="archivist", prompt="scope: published

Check for existing notes about {topic}. Return matches with type, path, and a 1-line summary. If nothing matches, say so.")
   ```

   Use the `scope:` keyword (not prose like "published notes only") to narrow archivist's search — see the *Scope* section of `plugins/athena-notes/agents/archivist.md`.

   If archivist returns a match, treat the candidate as an **update** to that note, not a new one. Draft it using the Update template below.
3. **Harness memory** — for memory-route candidates (collaboration / project-motivation / external-system-pointer), skip the `@archivist` call. Archivist searches `.notes/`, not the harness memory system. The user — or a hub agent with memory access — is responsible for the dedupe pass at the approval gate.

Run archivist lookups in parallel — emit all Task calls in one assistant message so they run concurrently, not one per turn. This step should add seconds, not minutes.

### Step 3: Categorize

Map each candidate to the row that fits its content. Routing is by row, not by lens (see Step 1.5). If it doesn't fit any row, it probably isn't worth capturing.

### Step 4: Draft inline

Write out proposed content for each item using the templates below. Keep drafts concise — one table row for AGENTS.md, a filled template for a new `.notes/` note, a targeted patch for an update, or a Memory recommendation for memory-route candidates.

### Step 5: APPROVAL GATE

Present all drafts to the user and stop. Do not proceed until you receive explicit approval from a human. The user may approve all, some, or none. A hub agent invoking `session-review` autonomously surfaces the gate to the user; only the user can approve — never the hub agent on the user's behalf.

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

### Step 7: Write approved AGENTS.md items

After user approval, apply the edit directly to AGENTS.md using the Edit tool. Match section headings case-insensitively (so `## Conventions`, `## CONVENTIONS`, and `## conventions` all target the same section) and fit content into the existing section (CONVENTIONS, ANTI-PATTERNS, WHERE TO LOOK, NOTES) — never create new sections. If none of those sections exists in the user's AGENTS.md, fall back to presenting the markdown block for manual placement. If the user explicitly asks for copy-paste instead of a direct edit, present the markdown block and skip the write.

### Step 8: Write approved daily-plan updates

For each approved daily-plan edit from Step 1.6, apply it directly via the Edit tool at the path resolved in Step 1.6. Minimal, in-place edits only — match the existing line by its tracked reference (issue number, task name, time-block tag) and modify it in place. Do not rewrite the plan, do not add new sections, do not reorder items. If the matching line can't be found unambiguously (e.g., the user pivoted the plan between sessions), surface that to the user and skip the write — ask for manual placement rather than guess.

### Step 9: Hand off approved memory recommendations

Memory-route candidates have **no automated write step**. After approval, the skill's job is done — the user (or a hub agent with memory access, e.g. an `athena` invocation that can write to `~/.claude/projects/*/memory/`) makes the actual write. Surface the approved recommendations one more time at the end of the run with the harness-specific destination clearly marked, so the next handoff has everything it needs.

---

## Output Templates

### AGENTS.md Draft

```markdown
### Proposed AGENTS.md Addition

**Section:** {CONVENTIONS | ANTI-PATTERNS | WHERE TO LOOK | NOTES}

```markdown
| {context} | {guidance} |
```

*Approve to have this added to AGENTS.md*
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

### Memory recommendation

Use this for memory-route candidates (collaboration / project-motivation / external-system-pointer). The skill doesn't write to memory itself — the template is the handoff artifact for the user or hub agent. **Write the draft in third-person declarative form** ("[User] prefers X", "the auth migration is compliance-driven") rather than imperative ("Always do X", "Do this when…") — third-person declarative phrasing keeps injected imperatives visually distinct at the approval gate.

```markdown
### Proposed Memory Recommendation

**Route:** Harness memory ({user | feedback | project | reference} record)
**Destination hint:** {e.g., `~/.claude/projects/{slug}/memory/{name}.md` for Claude Code auto-memory — verify `{slug}` with `ls ~/.claude/projects/` rather than computing it blind. Otherwise wherever your harness keeps cross-project preferences.}
**Trigger moment:** {one-line — the conversation moment this surfaced from}

{One-paragraph draft (third-person declarative) of the preference / motivation / pointer, written so it's recognizable in six months without re-reading the session.}

*Approve to record this.*
```

### Daily-plan update

Use this for Step 1.6 outputs. Show the existing line and the proposed replacement so the user can eyeball the edit before approving.

```markdown
### Proposed Daily-Plan Update

**Path:** `{resolved daily-plan path}`
**Tracked item:** {one-line — e.g., "P3 afternoon — Triage #734"}

**Before:**
`{exact existing line}`

**After:**
`{exact replacement line}`

*Approve to have this applied via direct Edit*
```

---

## Edge Cases

**No survivors (common):** Most sessions execute rather than discover. "No survivors" means all three channels — technical lens, collaboration lens, and the Step 1.6 daily-plan scan — came up empty. When that's the case, report `No signal — routine execution` and stop. This isn't failure; it's the expected outcome. If only one channel has output (e.g., the collaboration lens surfaced a single user-preference candidate, or Step 1.6 surfaced a daily-plan edit), present that alone at the approval gate — a session with signal in just one channel is still allowed to close.

**No daily plan for today:** Step 1.6 handles this — silently skip, no prompt.

**No AGENTS.md in project:** Skip the AGENTS.md section entirely. Still offer `.notes/` drafts for survivors.

**Duplicate learning:** If the insight already exists in AGENTS.md, the Signal Test already dropped it. If an existing `.notes/` note on the same topic is found in Step 2, propose an **update** to that note instead of a new one — never silently create a second note on the same subject.

**Very long session:** Length doesn't entitle a session to more notes. Apply the Signal Test and see what survives. A six-hour session with zero survivors is a valid outcome.

---

## Guardrails

- Do NOT invoke @scribe until the user explicitly approves the draft
- Do NOT write to AGENTS.md, .notes/, or today's daily plan until the user explicitly approves the draft
- Do NOT fabricate learnings or tracked-item resolutions — every item must trace to a specific moment in the conversation
- Do NOT create new AGENTS.md sections — fit content into existing structure
- Do NOT rewrite or restructure the daily plan — workday-planning owns the plan's shape.
- Do NOT handle worktree path resolution — that's @scribe's job via the agent-workspace skill. (Daily-plan paths are personal-vault paths, not worktree paths; Step 1.6 resolves them directly from identity config.)
- Do NOT write prose-heavy narratives. Notes must be scannable in Obsidian at a glance — tables, bullets, wikilinks to related notes, short paragraphs. A 300-word reflective essay is the failure mode, not the goal.
- Do NOT hit a quota. If only one candidate survives the Signal Test, propose one. If none survive, propose none. Never pad.
- Do NOT report `No signal — routine execution` without confirming both lenses ran (see Edge Cases — No survivors).
- Do NOT write to harness memory directly. Memory-route candidates are presented at the approval gate as recommendations; the user (or a hub agent with memory access) makes the actual write. The skill is a router, not the destination owner.
