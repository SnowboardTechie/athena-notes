# Interactive flow — no-args, gates, handoff dialogues

Loaded by [`/capture`](../SKILL.md) when an interactive surface is needed: the no-args entry, the medium/low confidence gate (Step 3), and the MEETING handoff (Step 4). Concentrating the user-facing dialogues here means future UX tuning lands in one place.

---

## No-args entry

Triggered when `/capture` is invoked with no body.

Prompt:

> *"What do you want to capture?"*

Accept the user's next reply as the body. Treat it as a freeform input — run detection in Step 2 just as for an argful invocation.

**If the reply is empty or whitespace** — re-prompt once:

> *"Capture body can't be empty — paste the thought, or send `abort` to stop."*

A second empty reply → stop, report `"Capture aborted (empty body)."`

**If the reply is `abort` / `cancel` / `stop`** — stop without writing. Report `"Capture aborted."`

The no-args entry is the lowest-friction surface. Don't add a second prompt asking for the type — let detection handle it. If detection lands in medium/low confidence, the Step 3 gate fires as normal.

---

## Step 3: Confidence gate

Triggered when detection returns `medium` or `low` confidence.

### `AskUserQuestion` invocation shape

For medium confidence (top 2 candidates):

```
AskUserQuestion(
  questions: [
    {
      question: "This looks like a {primary} or an {secondary}. Which type should it be?",
      header: "Note type",
      options: [
        { label: "{primary}",   description: "{one-line description of primary type}" },
        { label: "{secondary}", description: "{one-line description of secondary type}" }
      ],
      multiSelect: false
    }
  ]
)
```

For low confidence (top 3 candidates): same shape with three options instead of two.

The tool auto-provides an "Other" option for free-form input; do not add it manually.

### Option labels and descriptions

Use the type's display name as the label (`Idea`, `Decision`, `Exploration`, `Session`, `Thread`, `Task`). The description gives a one-line distinction to help the user pick:

| Type | Description |
|---|---|
| `Idea` | A spark — capture now, refine later. |
| `Decision` | A choice was made; record what and why. |
| `Exploration` | Thinking through options or tradeoffs. |
| `Session` | A summary of conversation or work. |
| `Thread` | A meta-note connecting related ideas across notes. |
| `Task` | A work item or ticket-tracked thread. |

### Handling the reply

- **User picks one of the listed options** → bake that type, proceed to Step 4 (or Step 5 if not MEETING).
- **User picks `Other` and types a known type** (case-insensitive match against the seven types) → bake that type, proceed.
- **User picks `Other` and types an unknown value** — re-ask once:

  > *"`{value}` isn't a recognized note type. Pick one of: idea, exploration, decision, session, thread, task. Or send `meeting` to redirect to /meeting-sync."*

  A second unknown value → fall back to the detector's primary candidate, report the fallback in Step 7's user-facing summary:

  > `ⓘ Used detector's primary type ({primary}) — your input "{value}" wasn't recognized.`

- **User responds with silence / ambiguity** → re-prompt with the same `AskUserQuestion`. Treat silence as a re-prompt, not as a default.

---

## Step 4: MEETING handoff dialogue

Triggered when the resolved type is MEETING.

### Initial offer

> This looks like meeting notes (attendees / decisions / action items detected). The `/meeting-sync` skill routes meeting blobs into a MEETING anchor plus DECISION / TASK / IDEA spin-offs. Want to switch over?
>
> *[switch to /meeting-sync / capture as a single SESSION note anyway / abort]*

Three accepted replies — three branches:

### Branch: `switch to /meeting-sync`

Respond:

> Run `/meeting-sync` and paste the same text. The skill will walk you through the anchor + spin-offs.

Stop. Do not invoke `/meeting-sync` from inside `/capture` — nested slash-command invocation is awkward in Claude Code, and the user's re-invocation is the natural next step.

### Branch: `capture as a single SESSION note anyway`

Force the type to SESSION, skip Step 5 (no archivist pre-link for SESSION), proceed to Step 6 with the body intact. Scribe will apply the SESSION template from [`cairn-notes/SKILL.md`](../../cairn-notes/SKILL.md), which has frontmatter-only attendees handling — adequate but not ideal for meeting content.

Report in Step 7:

> `✓ Captured as SESSION (you opted out of /meeting-sync routing)`

### Branch: `abort`

Stop without writing. Report `"Capture aborted."`

### Branch: silence or ambiguous reply

Re-prompt with the same three options. Don't fall through to a default — the MEETING handoff is intentional.

---

## Edge case: detection misfires mid-gate

If during Step 3 the user picks `Other` and types `meeting`, treat it as if MEETING had been detected initially — pivot to Step 4 (MEETING handoff) before any write. The gate's job is to land the right type; if the user's free-form answer steers into MEETING territory, the handoff still applies.

---

## Edge case: user wants a different surface entirely

If during any interactive turn the user types `/recall ...` or another slash command, treat it as a redirect: stop the `/capture` flow without writing, report `"Capture cancelled — running /recall instead."` (substituting whatever skill the user named), and let the harness pick up the new command on the next turn.

This is rare but matches the user's likely intent: they realized capture is the wrong surface.
