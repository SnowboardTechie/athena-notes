---
name: session-review
description: Review conversation sessions for project-specific learnings to document in AGENTS.md and .notes/
---

# Session Review

Surface learnings from this conversation worth preserving. Not a log of activity — a filter for signal.

Focus on 3-5 significant insights. If nothing stands out, say so.

---

## Quick Reference

```
/session-review    # review this session for learnings to capture
```

---

## Philosophy

Good sessions produce knowledge that shouldn't live only in your head. This skill finds that knowledge and routes it to the right place. The goal is signal, not completeness — a session with one sharp insight is better documented than one with ten mediocre ones.

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

Read back through the session. Look for moments where something was discovered, decided, or clarified. Ignore routine task execution. Flag 3-5 candidates max.

### Step 2: Read existing AGENTS.md

Check the project's AGENTS.md (if it exists) before drafting anything. Understand the current sections. Skip any learning that's already captured there.

### Step 3: Categorize

Map each candidate to a row in the table above. If it doesn't fit any row, it probably isn't worth capturing.

### Step 4: Draft inline

Write out proposed content for each item using the templates below. Keep drafts concise — one table row for AGENTS.md, a filled template for .notes/.

### Step 5: APPROVAL GATE

Present all drafts to the user and stop. Do not proceed until you receive explicit approval. The user may approve all, some, or none.

### Step 6: Write approved .notes/ items

For each approved .notes/ item, invoke @scribe:

```
Task(subagent_type="scribe", prompt="Write a {TYPE} note titled '{title}'. Content: {draft content}")
```

Scribe writes immediately on invocation — no preview, no confirmation. Only call it after the user approves.

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

### .notes/ Draft

```markdown
### Proposed .notes/ Entry

**Type:** {DECISION | EXPLORATION | SESSION}
**Filename:** `{YYYY-MM-DD}-{type}-{slug}.md`

{Draft content using the athena-notes template for that type}

*Approve to have @scribe write this note*
```

---

## Edge Cases

**Empty session:** "No significant learnings worth documenting this session."

**No AGENTS.md in project:** Skip the AGENTS.md section entirely. Still offer .notes/ drafts if applicable.

**Duplicate learning:** If the insight already exists in AGENTS.md, skip it. Don't propose adding something that's already there.

**Very long session:** Don't try to be comprehensive. Pick the 3-5 most significant moments and document those. A shorter, sharper review beats an exhaustive one.

---

## Guardrails

- Do NOT invoke @scribe until the user explicitly approves the draft
- Do NOT write to AGENTS.md directly — always present as copy-paste markdown
- Do NOT fabricate learnings — every item must trace to a specific moment in the conversation
- Do NOT create new AGENTS.md sections — fit content into existing structure
- Do NOT handle worktree path resolution — that's @scribe's job via the agent-workspace skill
