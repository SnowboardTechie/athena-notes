# Type detection — signals and tiers

Loaded by [`/capture`](../SKILL.md) Step 2 when classifying freeform input. Keep this reference open while making detection-tier judgments; the signal table is the source of truth.

The detector reads the captured body and returns `(type, confidence)` where confidence is `high`, `medium`, or `low`. This is a heuristic — ship the simple version, tune from observed false-positives.

---

## Signal table

| Type | Strong signals | Weak signals |
|---|---|---|
| **IDEA** | starts with `what if`, `thought:`, `spark:`, `idea:` | very short body (< 2 sentences); speculative tone; no decisive verb |
| **DECISION** | contains `decided`, `going with`, `we'll go with`, `chose`, `let's use`, `I'll switch to`, `we picked` | definite past or imperative tense; single named outcome; rationale clause |
| **EXPLORATION** | contains `vs.`, `options:`, `tradeoffs`, `looking at`, `weighing`, `comparing` | longer body (> 2 paragraphs); comparison shape; multiple named candidates |
| **SESSION** | starts with `session summary`, `we just covered`, `today I worked on`, `recap:` | references the current conversation explicitly; multi-topic |
| **THREAD** | starts with `thread:`, `this keeps coming up`, `pattern across`; body explicitly enumerates multiple existing wikilinks | meta-note tone; "I've noticed…" framing |
| **TASK** | ticket id (`#123`, `[A-Z]+-\d+`); contains `blocker`, `PR #`, `checking status`, `following up on` | imperative future tense scoped to a single ticket; status framing |
| **MEETING** | matches [meeting-sync's shape check](../../meeting-sync/SKILL.md#shape-check) — attendee-like line, decision-shape language, action-item shape, or meeting header | _(none — MEETING is shape-driven, not keyword-driven)_ |

Order of evaluation: MEETING shape check first (because its branch is a handoff, not a write), then the other six in any order. If multiple types match strongly, the tier downgrades from `high` to `medium`.

---

## Confidence tiers

### `high`

At least one strong signal **and** the body fits the type's shape. The detector is sure enough that re-asking would be friction without value.

- DECISION: contains `decided` *and* names a single outcome in one sentence.
- EXPLORATION: contains `vs.` or `tradeoffs` *and* is > 2 paragraphs with multiple named candidates.
- IDEA: starts with `what if` or `idea:` *and* is < 3 sentences.
- TASK: contains a ticket id *and* the body is scoped to that ticket.
- SESSION / THREAD: starts with the explicit prefix in the strong-signals column.
- MEETING: any shape-check positive (treated as high — MEETING always handoffs).

→ Skip the Step 3 confidence gate. Proceed directly to Step 4.

### `medium`

One strong signal, but a second type has a competing signal — ambiguity worth one user-facing confirmation.

Common pairs:
- DECISION ↔ EXPLORATION — body contains `decided` but also `tradeoffs`; could be either "I decided" or "exploring why I decided."
- IDEA ↔ DECISION — body starts with `what if` but also names a chosen outcome (`what if we go with X`).
- TASK ↔ IDEA — body mentions a ticket id but the framing is speculative (`what if #123 should…`).

→ Run Step 3 with the top 2 candidates as `AskUserQuestion` options. The `AskUserQuestion` tool auto-provides "Other."

### `low`

No strong signals, or competing strong signals across three or more types.

- Body is short and abstract (e.g., `/capture sonnet 4.6 default`).
- Body is long but evenly mixed in tone.

→ Run Step 3 with the top 3 candidates. The `AskUserQuestion` tool auto-provides "Other."

---

## Worked examples

### High-confidence DECISION

> `/capture we decided to switch the default model to Sonnet 4.6 — Haiku 4.5 hits rate limits in CI`

- Strong signal: `decided`
- Shape: single named outcome (Sonnet 4.6), rationale clause (rate limits in CI), one sentence
- → `(DECISION, high)` — skip gate, proceed to pre-link

### High-confidence EXPLORATION

> `/capture Looking at JWT vs session tokens for the new API. JWT wins on statelessness but loses on revocation; session tokens give us instant revoke but need a store. Leaning JWT with short expiry + refresh, but…`

- Strong signals: `Looking at`, `vs.`, `tradeoffs` shape
- Shape: > 2 sentences, multiple candidates, comparison structure
- → `(EXPLORATION, high)` — skip gate, proceed to pre-link

### Medium-confidence DECISION ↔ EXPLORATION

> `/capture we decided JWT but the tradeoffs around revocation are still nagging me`

- Strong signal: `decided` (DECISION)
- Competing signal: `tradeoffs` (EXPLORATION)
- → `(DECISION, medium)` with EXPLORATION as secondary
- Step 3 gate: *"This looks like a Decision or an Exploration. Which type should it be?"*

### Low-confidence

> `/capture sonnet 4.6 default`

- No strong signals; short and abstract
- Plausible: IDEA (spark), DECISION (decided to use Sonnet), TASK (work item to switch)
- → `(IDEA, low)` with DECISION and TASK as secondaries
- Step 3 gate with three options + auto-provided "Other"

### MEETING shape

> `/capture Standup notes: Alice, Bob, me. Decided to push the release to Friday. Bob to update the changelog. Alice owns the migration script. Open: do we still need the staging soak?`

- Meeting-sync shape check passes: attendee-like line ("Alice, Bob, me"), decision-shape (`Decided to`), action-item shape (`Bob to update`, `Alice owns`), open-question marker
- → `(MEETING, high)` — proceed to Step 4 MEETING handoff (does not write)
