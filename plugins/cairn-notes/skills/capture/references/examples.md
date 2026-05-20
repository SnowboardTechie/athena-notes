# Examples — four end-to-end captures

Loaded by [`/capture`](../SKILL.md) on request, or when an implementer or new contributor wants worked examples to match shapes against. Each example walks the full Step 1–7 flow.

---

## Example 1: Freeform DECISION (high-confidence, pre-linked)

**User invokes:**

```
/capture we decided to switch the default model to Sonnet 4.6 — Haiku 4.5 hits rate limits in CI
```

**Step 1 — Resolve input form.** Freeform (no `<type>:` prefix). Body is the full args.

**Step 2 — Detect type.** Strong signal `decided` + single named outcome + rationale clause → `(DECISION, high)`.

**Step 3 — Confidence gate.** Skipped (high confidence).

**Step 4 — MEETING handoff.** Skipped (type is DECISION, not MEETING).

**Step 5 — Pre-link via archivist.** DECISION fires the pre-link. Dispatch archivist and **await its response** before composing Step 6 — the scribe prompt depends on archivist's wikilinks. Archivist Task call:

```
Task(subagent_type="archivist", prompt="scope: published

Find notes related to this capture: switching the default model to Sonnet 4.6 because Haiku 4.5 hits rate limits in CI. Return up to 5 wikilinks with one-line relevance notes.")
```

Archivist returns:

```
**[[decision-default-model]]** (decision)
- Previously decided: Haiku 4.5 as default
- *Relevance: Direct prior decision; this capture supersedes it*

**[[exploration-ci-rate-limits]]** (exploration)
- Documented CI rate-limit hits across model versions
- *Relevance: Background context for the new decision*
```

Take top 2 (only 2 returned). Inline into Step 6.

**Step 6 — Dispatch scribe.** After archivist's response is in hand, in the next assistant turn:

```
Task(subagent_type="scribe", prompt="Write a DECISION note. Body:

We decided to switch the default model to Sonnet 4.6 — Haiku 4.5 hits rate limits in CI.

Related notes: [[decision-default-model]], [[exploration-ci-rate-limits]]")
```

Scribe applies the DECISION template, slugs the filename, writes:

```
Wrote: decisions/default-model-sonnet-4-6.md
Type: permanent (decision)
```

**Step 7 — Report:**

```
✓ Captured as DECISION: [decisions/default-model-sonnet-4-6.md](.notes/decisions/default-model-sonnet-4-6.md)

Switched default model from Haiku 4.5 to Sonnet 4.6 due to CI rate-limit hits.

→ Linked: [[decision-default-model]], [[exploration-ci-rate-limits]]
```

---

## Example 2: Explicit-prefix IDEA (no detection, no pre-link)

**User invokes:**

```
/capture idea: what if forge could read planning sources from a per-project file instead of the global one
```

**Step 1 — Resolve input form.** Explicit prefix `idea:`. Strip the prefix; force type to IDEA. Skip Step 2.

**Step 2 — Detect type.** Skipped (explicit prefix).

**Step 3 — Confidence gate.** Skipped (forced type).

**Step 4 — MEETING handoff.** Skipped (type is IDEA).

**Step 5 — Pre-link via archivist.** Skipped (IDEA doesn't pre-link — speed > linkage).

**Step 6 — Dispatch scribe.**

```
Task(subagent_type="scribe", prompt="Write a IDEA note. Body:

What if forge could read planning sources from a per-project file instead of the global one")
```

Scribe writes:

```
Wrote: ideas/forge-per-project-planning-sources.md
Type: permanent (idea)
```

**Step 7 — Report:**

```
✓ Captured as IDEA: [ideas/forge-per-project-planning-sources.md](.notes/ideas/forge-per-project-planning-sources.md)

Sparked: forge could read planning sources from a per-project file instead of the global one.
```

(No `→ Linked:` line — IDEA skips pre-link.)

---

## Example 3: No-args interactive (medium confidence, gated)

**User invokes:**

```
/capture
```

**Step 1 — Resolve input form.** Empty args → no-args interactive. Prompt:

> *"What do you want to capture?"*

**User replies:**

> `we decided JWT but the tradeoffs around revocation are still nagging me`

**Step 2 — Detect type.** Strong signal `decided` (DECISION). Competing signal `tradeoffs` (EXPLORATION). Ambiguity → `(DECISION, medium)` with EXPLORATION as secondary.

**Step 3 — Confidence gate.** `AskUserQuestion`:

> *"This looks like a Decision or an Exploration. Which type should it be?"*
> Options: `Decision`, `Exploration` (+ auto-provided `Other`)

**User picks:** `Exploration`.

Force type to EXPLORATION. Proceed.

**Step 4 — MEETING handoff.** Skipped.

**Step 5 — Pre-link via archivist.** EXPLORATION fires the pre-link.

```
Task(subagent_type="archivist", prompt="scope: published

Find notes related to this capture: exploring JWT vs session tokens and the tradeoffs around revocation. Return up to 5 wikilinks with one-line relevance notes.")
```

Archivist returns one match:

```
**[[exploration-auth]]** (exploration)
- Earlier auth exploration, JWT preferred for stateless
- *Relevance: Same topic, earlier framing*
```

**Step 6 — Dispatch scribe.**

```
Task(subagent_type="scribe", prompt="Write a EXPLORATION note. Body:

We decided JWT but the tradeoffs around revocation are still nagging me.

Related notes: [[exploration-auth]]")
```

Scribe finds `exploration-auth.md` exists; per Note Reuse Protocol, updates it instead of creating a new file:

```
Wrote: explorations/exploration-auth.md
Type: permanent (exploration) — updated existing note
```

**Step 7 — Report:**

```
✓ Updated existing note: [explorations/exploration-auth.md](.notes/explorations/exploration-auth.md)

Added the revocation-tradeoff thread to the existing JWT exploration.

→ Linked: [[exploration-auth]]

(All three examples above are invoked from inside a project repo — `.notes/` prefix applied per Step 7's path-prefixing table. If Example 2 were invoked from `~/notes/{{PERSONAL_VAULT}}/` directly, the href would be `ideas/forge-per-project-planning-sources.md` with no prefix.)
```

(Scribe's reuse-over-duplicate behavior is honored — the Step 7 verb is "Updated," not "Captured.")

---

## Example 4: MEETING-shape redirect

**User invokes:**

```
/capture Standup notes: Alice, Bob, me. Decided to push the release to Friday. Bob to update the changelog. Alice owns the migration script. Open: do we still need the staging soak?
```

**Step 1 — Resolve input form.** Freeform.

**Step 2 — Detect type.** Meeting-sync's shape check passes on multiple signals: attendee-like line (`Alice, Bob, me`), decision-shape (`Decided to`), action-item shape (`Bob to update`, `Alice owns`), open-question marker (`Open:`). → `(MEETING, high)`.

**Step 3 — Confidence gate.** Skipped.

**Step 4 — MEETING handoff.** Fires. Present:

> This looks like meeting notes (attendees / decisions / action items detected). The `/meeting-sync` skill routes meeting blobs into a MEETING anchor plus DECISION / TASK / IDEA spin-offs. Want to switch over?
>
> *[switch to /meeting-sync / capture as a single SESSION note anyway / abort]*

**User replies:** `switch to /meeting-sync`.

**Step 4 branch — switch.** Respond:

> Run `/meeting-sync` and paste the same text. The skill will walk you through the anchor + spin-offs.

Stop. No write happens. Steps 5–7 are skipped.

(If the user had replied `capture as a single SESSION note anyway`, the flow would proceed to Step 6 with type SESSION and no pre-link, producing one SESSION note containing the full meeting blob — suboptimal but valid.)
