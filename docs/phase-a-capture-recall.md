# Phase A — `/capture` and `/recall` design

Durable reference for the Phase A implementation session. Phase A ships two new user-facing skills (`/capture`, `/recall`) and one prerequisite extension to the `archivist` agent. No removals, no doc rewrites — those are Phase B.

Tracking: [#86](https://github.com/SnowboardTechie/cairn-notes/issues/86) → Phase A. Plan: [`.claude/plans/she-is-scaffolding-inside-iterative-flamingo.md`](../.claude/plans/she-is-scaffolding-inside-iterative-flamingo.md) (not in repo; lives in the user's local plans dir). Predecessor PR: [#87](https://github.com/SnowboardTechie/cairn-notes/pull/87) (Phase 0.5 rename — merged).

---

## Why this doc exists

The Phase A *decisions* — type-detection tiers, vault routing, archivist extension shape — were worked out in a prior planning conversation that did not persist. Phase A implementation cannot start without that design durable somewhere. This doc captures it so the next session can open a single skill body and execute against a written spec, not a re-derivation.

Scope of this doc: design only. No skill bodies, no agent edits. The implementation session creates `plugins/cairn-notes/skills/capture/` and `plugins/cairn-notes/skills/recall/` and edits `plugins/cairn-notes/agents/archivist.md` against the shapes described here.

---

## Background

Phase 0.5 renamed the plugin to `cairn-notes`. The capture-first reframing repositions the plugin around two new user-facing surfaces:

- **`/capture`** — wraps `scribe` so a user can write directly into the vault without an Athena hop.
- **`/recall`** — wraps `archivist` so a user can search directly.

Both skills defer to existing infrastructure:

- Note templates live in [`plugins/cairn-notes/skills/cairn-notes/SKILL.md`](../plugins/cairn-notes/skills/cairn-notes/SKILL.md). `/capture` does not duplicate them; `scribe` already loads them.
- Vault resolution (Project / Direct vault / Default) lives in [`plugins/cairn-notes/agents/scribe.md`](../plugins/cairn-notes/agents/scribe.md). `/capture` does not handle vault paths; scribe does.
- Worktree-aware trunk-root resolution lives in [`plugins/cairn-notes/agents/archivist.md`](../plugins/cairn-notes/agents/archivist.md). `/recall` does not duplicate it.

The new skills are thin orchestrators that classify intent, dispatch the right spoke(s), and present results. The heavy lifting is already in place.

---

## Archivist `vault:` extension (prerequisite)

`/recall scope:both` needs the archivist to search a vault *other than* the current project's `.notes/`. Today, archivist resolves `{TRUNK_ROOT}/.notes/` from `git rev-parse --git-common-dir` and searches there exclusively. The extension adds a first-line `vault:` directive — same shape as the existing [`scope:` keyword](../plugins/cairn-notes/agents/archivist.md) — that overrides the resolution.

### Signature

A `vault:` directive sits on the first non-empty line, parallel to (and independent of) `scope:`. Either, both, or neither may be present. When both are present, order doesn't matter; the parser consumes both before the blank-line separator that precedes the query.

| Keyword | Resolved root | Use when |
|---|---|---|
| `vault: project` | Current repo's trunk `.notes/` via `git rev-parse --git-common-dir` (today's behavior) | Default — caller is searching the codebase's local vault |
| `vault: personal` | `~/notes/{{PERSONAL_VAULT}}/` read from `~/.claude/cairn/identity.md` | Caller is searching the user's cross-project / personal-knowledge vault |
| `vault: <absolute-path>` | The supplied path (must start with `/` and end at a directory containing `.notes/` or be the vault root itself) | Caller is searching another project's vault by path — e.g., `vault: /Users/bryan/notes/another-project` |

When no `vault:` line is present, the current trunk-root resolution applies. This keeps every existing caller (meeting-sync, scribe-internal lookups in the future, manual archivist invocations) backward-compatible.

### Resolution rules

- **`vault: project`** — identical to today's path. The bash call, the suffix-strip, the error paths (not a git repo, `.notes/` missing) all stay.
- **`vault: personal`** — read `~/.claude/cairn/identity.md`, parse `personal_vault: <name>`, resolve to `${HOME}/notes/<name>/`. If `identity.md` is missing or unreadable, report `"vault not accessible — personal vault not configured (run /cairn-setup)"` and return without searching. Do not fall back to `~/notes/second-brain/` silently — the caller deserves to know the difference between "configured vault has no results" and "no vault configured."
- **`vault: <absolute-path>`** — accept iff the path starts with `/`, does not contain `..`, and the resolved directory exists. On any failure, report `"vault not accessible — path {path} not found"` and return. Relative paths are rejected up front (no `cd`, no shell expansion).

In all three cases, the resolved root is used as the prefix for the search strategies' `path=` arguments, exactly as `{TRUNK_ROOT}/.notes/` is used today. Strategies, response format, scope-keyword behavior — unchanged.

### Reporting

The existing `## Search Method` block already reports `Scope applied: …`. Add a parallel line: `Vault searched: project | personal | {path}` so a `scope:both` caller's two parallel archivist invocations can be distinguished in the merged output.

### LOC budget

~20 LOC against the current [archivist.md](../plugins/cairn-notes/agents/archivist.md): a new "Vault" subsection paralleling the existing "Scope" subsection, plus a 3-line block in "Startup — Resolve Trunk Root" branching on the directive. The existing strategies, response format, and bash-hygiene rules are untouched.

### Backward compatibility

Every existing caller (meeting-sync Step 3, future scribe lookups, any user invoking `@archivist` directly) sends no `vault:` line and receives today's behavior. The extension is purely additive at the call site — same as `scope:` was when it landed.

---

## `/capture` design

### Purpose

Primary user-facing capture entry. Replaces the implicit "talk to Athena, she'll decide what type and call scribe" flow with a direct `/capture <text>` surface. Auto-classifies, optionally pre-links related notes, dispatches scribe.

### Three input forms

| Form | Example | Behavior |
|---|---|---|
| **Freeform** | `/capture we should probably switch the default model to Sonnet 4.6 since Haiku 4.5 is hitting the rate limits in CI` | Auto-detect type from the body; route per confidence tier |
| **Explicit-prefix** | `/capture decision: switching default model to Sonnet 4.6 — Haiku 4.5 hits rate limits in CI` | Force the named type; skip detection; write directly |
| **No-args** | `/capture` | Prompt `"What do you want to capture?"`, accept the answer, then proceed as freeform |

The freeform form is the common case. Explicit-prefix is for users who already know the type and want to skip the detection step. No-args is the lowest-friction entry point — type "/capture", hit enter, then write.

#### Explicit-prefix parsing

Match `^\s*(idea|exploration|decision|session|thread|task|meeting)\s*:\s*` against the start of the args, case-insensitive. On match: strip the prefix, force the type, skip §"Type detection." The remaining text is the body. If the prefix is `meeting:`, go straight to the MEETING handoff (§"MEETING-shape handoff") — explicit prefix doesn't bypass the routing, only the detection.

### Type detection

For freeform and no-args inputs, classify the body by inspecting it for signals from each type. Each signal is a substring or shape pattern — not a regex contest. The detector returns a `(type, confidence)` tuple.

#### Signals per type

| Type | Strong signals | Weak signals |
|---|---|---|
| **IDEA** | starts with "what if", "thought:", "spark:", "idea:" | very short (< 2 sentences), speculative tone, no decisive verb |
| **DECISION** | contains "decided", "going with", "we'll go with", "chose", "let's use", "I'll switch to" | definite past or imperative tense, single named outcome |
| **EXPLORATION** | contains "vs.", "options:", "tradeoffs", "looking at", multiple paragraphs | longer body (> 2 paragraphs), comparison shape |
| **SESSION** | starts with "session summary", "we just covered", "today I worked on" | references the current conversation explicitly |
| **THREAD** | starts with "thread:", "this keeps coming up", "pattern across" | references multiple existing wikilinks |
| **TASK** | contains a ticket id (`#123`, `[A-Z]+-\d+`), "blocker", "PR #", "checking status" | imperative future tense scoped to a single ticket |
| **MEETING** | meeting-sync's [shape check](../plugins/cairn-notes/skills/meeting-sync/SKILL.md#shape-check) returns at least one positive signal | (none — MEETING is shape-driven, not keyword-driven) |

#### Confidence tiers

- **High** — at least one strong signal *and* the body fits the type's shape (e.g., DECISION with a single named outcome; EXPLORATION with > 2 paragraphs). Write immediately. No confirmation gate.
- **Medium** — one signal but ambiguity (e.g., "decided" appears, but the body could be an EXPLORATION of why the decision was made). Run an `AskUserQuestion` gate with the top 2 candidate types as options plus "Other" auto-provided.
- **Low** — no strong signals, or competing strong signals across types. Run the `AskUserQuestion` gate with the top 3 candidates.

The gate question reads: *"This looks like {primary} (or {secondary}). Which type should it be?"* — short labels (`Idea`, `Decision`, `Exploration`, etc.). Selecting one bakes the type; "Other" lets the user type a free-form type name (validated against the seven known types; unknown types prompt a re-ask).

The detection is deliberately heuristic. Bryan's review-by-feel feedback ("does this confirmation gate fire too often?") drives any future signal tuning — don't hand-roll a confidence score; ship the simple version, iterate on observed false-positives.

### MEETING-shape handoff

If detection (or explicit-prefix `meeting:`) selects MEETING, `/capture` does *not* call scribe. Instead, present:

> This looks like meeting notes (attendees / decisions / action items detected). The `/meeting-sync` skill routes meeting blobs into a MEETING anchor plus DECISION / TASK / IDEA spin-offs. Want to switch over? *[yes / capture as a single note anyway / abort]*

- **yes** — output `"Run /meeting-sync — paste the same text and approve the routing."` and stop. The user re-invokes meeting-sync; `/capture` does not chain into another slash command. Cleaner re-entry, no nested skill execution.
- **capture as a single note anyway** — fall back to a SESSION-shaped capture (single note, attendees in frontmatter if extractable, no spin-offs). Rare but valid; honors the user's override.
- **abort** — stop without writing.

This is the only branch where `/capture` refuses to write directly. Every other branch ends at scribe.

### Parallel archivist pre-link

For **DECISION** and **EXPLORATION** captures, fire an archivist Task call **in parallel** with drafting the scribe prompt — one assistant turn, both calls in the same message. The archivist returns wikilink candidates that get inlined into the scribe prompt as `Related notes: [[a]], [[b]]` so scribe can include them in the note's "Related" section.

For **IDEA**, **TASK**, **SESSION**, **THREAD**: skip the pre-link. Rationale: these are low-friction captures; an extra archivist round-trip adds latency without proportional value. IDEAs are about catching the spark; TASKs are usually scoped by ticket id (the linkage is in the title); SESSION and THREAD captures are explicit user acts where the user can name the links themselves.

#### Archivist call shape

```
Task(subagent_type="archivist", prompt="scope: published

Find notes related to the topic of this capture: {2-3 sentence summary of the body}. Return up to 5 wikilinks with one-line relevance notes.")
```

`scope: published` excludes `.notes/.agents/` so working drafts don't leak in. No `vault:` directive — the default (current repo's trunk vault) is what `/capture` wants. Multi-vault pre-linking is out of scope for v0.6.0.

If archivist returns no results, drop the "Related notes:" line from the scribe prompt entirely. Don't write "Related notes: (none found)" — that's noise in the note body.

If archivist fails (vault inaccessible, error path), proceed with scribe without pre-links and report the archivist failure in the final user-facing summary. Capture is the priority; linkage is best-effort.

### Scribe dispatch

After detection (and pre-link, when applicable):

```
Task(subagent_type="scribe", prompt="Write a {TYPE} note. Body:

{captured text}

{If pre-linked: Related notes: [[a]], [[b]], [[c]]}")
```

Scribe handles:

- Vault resolution (Project / Direct vault / Default per its three-mode detection)
- Note-reuse protocol (update existing note if title matches an existing slug)
- Folder selection (existing structure or cairn defaults)
- Template application (loads the cairn-notes reference skill)
- Filename slugging

`/capture` does not touch any of those. It only forwards `(type, body, related_links)`. Match meeting-sync's pattern: "trust scribe's resolution — don't pass explicit target paths."

### Result reporting

After scribe returns, present:

```
✓ Captured as {TYPE}: {markdown link to note path}

{1-2 line summary of what was written}
{Pre-linked: → [[note-1]], [[note-2]]   ← if pre-link ran}
```

The note path is a clickable markdown link (per the user's "preserve links" rule). No "Co-authored-by" trailers.

### Vault routing

`/capture` does not handle vault routing — it inherits scribe's three-mode detection. The natural consequence:

| Where invoked | Where the capture lands |
|---|---|
| Inside a project repo (cwd has `.git` and a `.notes/` symlink, or scribe auto-sets one up) | Project vault — `~/notes/{project}/` via `.notes` symlink |
| Inside `~/notes/{{PERSONAL_VAULT}}/` directly | Current directory |
| Anywhere else (not in a git repo, not in a vault) | Personal vault — `~/notes/{{PERSONAL_VAULT}}/` |

This matches meeting-sync's routing exactly. No `vault:` flag on `/capture` in v0.6.0; if a user wants to capture into the personal vault from a project repo, they `cd` first.

### File layout

```
plugins/cairn-notes/skills/capture/
  SKILL.md
  references/
    type-detection.md
    interactive-flow.md
    examples.md
```

- **`SKILL.md`** — the user-facing entry. Frontmatter (`name: capture`, description with triggers), Quick Reference, three input forms, the detection → gate → scribe pipeline as numbered steps, the MEETING handoff branch, result reporting, edge cases, guardrails.
- **`references/type-detection.md`** — the signal table above plus worked examples showing how each tier resolves. Loaded by `SKILL.md` on detection-tier branches; not surfaced inline so the main body stays scannable.
- **`references/interactive-flow.md`** — the no-args entry path, the medium/low-confidence `AskUserQuestion` shape, the MEETING handoff dialogue. Keeps interactive UX in one place where future UX tuning is concentrated.
- **`references/examples.md`** — three or four worked end-to-end captures: a freeform DECISION, an explicit-prefix IDEA, a no-args interactive session, a meeting-shape redirect. Mirrors the issue-create skill's "anchor: this mirrors well-written tickets the user writes by hand" pattern.

No `commands/capture.md` shim — per [AGENTS.md "Command files vs. skill auto-registration"](../plugins/cairn-notes/AGENTS.md#command-files-vs-skill-auto-registration), the bare slash form auto-registers. Adding a shim would shadow `/capture` and break it.

### Guardrails (paraphrasing the skill body's expected closing section)

- Do NOT duplicate note templates — defer to the cairn-notes reference skill via scribe.
- Do NOT pass an explicit vault path to scribe — let its three-mode detection resolve it.
- Do NOT chain into `/meeting-sync` inline; report the handoff and stop. The user re-invokes.
- Do NOT block on the archivist pre-link if it fails — capture is the priority.
- Do NOT add a `#cairn` brand tag to captured notes (per plan §"Open implementation questions").
- Do NOT add `Co-Authored-By:` trailers to note bodies.

---

## `/recall` design

### Purpose

User-facing retrieval. Wraps the archivist agent so a user can search the vault directly: `/recall what did we decide about default models`. Returns wikilinks, summaries, and (for single matches) the full note body inline.

### Query shape

Freeform query plus optional flags. The flag form is `key:value` at the start of args; flags can appear in any order; first non-flag token starts the query. Example:

```
/recall scope:both type:decision since:2026-04-01 default model
```

### Flags

| Flag | Values | Default | Behavior |
|---|---|---|---|
| `scope:` | `project`, `personal`, `both` | current-vault (resolved from cwd) | Which vault(s) to search |
| `type:` | `idea`, `exploration`, `decision`, `session`, `thread`, `task`, `meeting` | unfiltered | Filter results to one note type |
| `since:` | ISO date `YYYY-MM-DD` | unfiltered | Filter to notes with `date:` frontmatter on or after this date |
| `attendees:` | comma-separated names | unfiltered | Filter MEETING notes by attendee (implies `type:meeting`) |

#### `scope:` resolution

- **`scope:project`** (or default when cwd is a project repo) — single archivist call, no `vault:` directive (defaults to trunk-vault resolution).
- **`scope:personal`** (or default when cwd is `~/notes/{{PERSONAL_VAULT}}/`) — single archivist call with `vault: personal`.
- **`scope:both`** — two archivist calls in parallel (one assistant turn, two Task tool uses), one with `vault: project`, one with `vault: personal`. Results merged, grouped by vault in the response. The `vault:` extension is the prerequisite that makes this shape possible.

The default flips based on cwd: a `/recall` invoked from a project repo defaults to `scope:project`; from the personal vault, `scope:personal`. This matches the user's intuition — "search where I am, unless I say otherwise." Determining cwd uses the same `git rev-parse --git-common-dir` / `~/notes/{{PERSONAL_VAULT}}/` checks the existing tooling uses.

#### `type:` translation

The archivist's [Strategy 1: Frontmatter search](../plugins/cairn-notes/agents/archivist.md#strategy-1-frontmatter-search) already greps for `type: decision`-style markers. `/recall` builds the archivist prompt with an explicit instruction: `"Filter results to notes whose frontmatter contains 'type: {value}'."` No archivist-side schema change required.

#### `since:` translation

Two parsing modes:

- ISO date (`YYYY-MM-DD`) — explicit, unambiguous. Required for v0.6.0.
- Reject everything else — natural-language dates (`last week`, `yesterday`) are out of scope. If the user passes a non-ISO string, return: *"`since:` requires ISO date `YYYY-MM-DD`. Got `{input}`."*

`/recall` translates `since:2026-04-01` to a filename-prefix glob (`2026-{04..}-*` is awkward; simpler: pass the date to the archivist prompt and let it post-filter results by frontmatter `date:` field). The archivist's Read step already opens candidate files; adding a date-filter check in its existing flow is cheaper than another search strategy.

#### `attendees:` translation

Filters to MEETING notes (implies `type:meeting`) and adds an instruction to the archivist prompt: `"Within meeting notes, return only those whose attendees: frontmatter list includes ALL of: {names}."` Multi-attendee filter is an intersection — `attendees:bryan,alice` returns meetings where *both* attended.

### Archivist call shape

```
Task(subagent_type="archivist", prompt="scope: published
vault: {project|personal|<path>}

Find notes about: {query}.

Apply these filters:
- Type: {type or 'any'}
- Date on or after: {since or 'any'}
- Attendees (if MEETING): {names or 'any'}

Return up to 10 matches with type, wikilink, path, and a 1-line summary. If exactly one match, also include the full note body.")
```

The `"if exactly one match, also include the full note body"` instruction triggers the single-result auto-include — archivist already opens candidate files via Read, so returning the body is a small additional step in its existing flow.

`scope: published` is always passed. `--include-working` to expose `.agents/` working files is deferred to v0.7+; v0.6.0 ships published-only.

### Result formatting

Three cases:

**Zero results.**

```
No matches for "{query}".

{If scope:both, mention both vaults were searched.}
{Suggestions: try broader terms, check spelling, or `/capture` if this is a new topic worth recording.}
```

**Single result.** Auto-include the note body inline, similar to `gh issue view`:

```
1 match in {vault}:

[[note-slug]] — {type}
{path}

---

{full note body, including frontmatter}
```

**Multi-result.** List with type, wikilink, path, 1-line summary:

```
{N} matches in {vault}:

1. [[note-slug-a]] — decision — {path}
   {1-line summary}

2. [[note-slug-b]] — exploration — {path}
   {1-line summary}

...
```

For `scope:both` multi-result, group by vault with a section header per vault. Do not interleave — readers track their current scope by source.

After a multi-result list, do not prompt for "pick a number to view the body." The user re-invokes `/recall {slug}` if they want the body. Cleaner re-entry, less stateful UX. Revisit if friction surfaces.

### File layout

```
plugins/cairn-notes/skills/recall/
  SKILL.md
  references/
    query-shapes.md
    result-formatting.md
```

- **`SKILL.md`** — frontmatter, Quick Reference, flag parsing, archivist call shape, result-formatting branches, edge cases, guardrails.
- **`references/query-shapes.md`** — the flag-translation rules (how `type:`, `since:`, `attendees:` become archivist-prompt instructions). Concentrated in a reference so future flag additions land in one place.
- **`references/result-formatting.md`** — the three result-shape branches with worked examples. Loaded on the formatting step.

No `commands/recall.md` shim — same reasoning as `/capture`.

### Guardrails

- Do NOT search `.agents/` working files — always pass `scope: published`.
- Do NOT interleave results across vaults — group by `vault: project` vs `vault: personal`.
- Do NOT prompt the user to "pick a number" after a multi-result list — let them re-invoke if they want body inline.
- Do NOT accept non-ISO `since:` values — reject with a clear error.
- Do NOT search across more than two vaults in v0.6.0 — `scope:both` is the maximum cardinality. Cross-project recall ("show me decisions across every project vault I have") is deferred.

---

## Open implementation questions

These are flagged decisions — defaults are set but each could merit a one-line override from Bryan during implementation. Listed roughly in order of likelihood-to-revisit.

| # | Question | Default for v0.6.0 | Why it might change |
|---|---|---|---|
| 1 | Detection signal table — what counts as "strong" vs "weak"? | Ship the table in §"Type detection"; iterate on observed false-positives | Bryan's first ~10 captures are the real test; the gate fires too often or not often enough → tune signals |
| 2 | Medium/Low confidence gate — show top 2 or top 3 candidate types? | Top 2 for medium, top 3 for low | If 3 always feels noisy, drop to 2 across the board |
| 3 | MEETING handoff — does `/capture` chain into `/meeting-sync`, or just suggest it? | Suggest it; user re-invokes | Re-entry friction observed → revisit chaining (but skill-from-skill invocation is awkward in Claude Code) |
| 4 | `/recall` default scope — current vault, or both? | Current vault (project from a repo, personal from `~/notes/{{PERSONAL_VAULT}}/`) | If Bryan's common query crosses vaults, flip default to `both` |
| 5 | `/recall` `since:` natural-language parsing | ISO only; reject `last week` | If "last week" becomes a frequent ask, add a small parser; ISO stays canonical |
| 6 | `/recall` multi-result UX — list-only, or "pick a number"? | List-only; user re-invokes for body | If re-invocation feels tedious, add `/recall #N` shorthand or a numbered pick |
| 7 | Archivist `vault:` — three values (project, personal, abs-path) or two (project, personal)? | Three; abs-path is the escape hatch | If abs-path is never used (or is a footgun), drop it |
| 8 | `/capture` SESSION-of-current-chat | Out of scope for v0.6.0 — explicit prefix only | If "summarize this conversation" becomes a common no-args ask, add a SESSION-from-context mode (would need access to harness transcript, not trivial) |
| 9 | `/capture` title derivation — first N words, LLM summary, or always ask? | First sentence of body → kebab-case via scribe's existing slug rules (today's scribe behavior) | If slugs feel bad, override with an LLM-summarized title at /capture layer before passing to scribe |
| 10 | `/capture` archivist pre-link — fire for IDEA too? | Only DECISION + EXPLORATION | If users want every capture linked, expand; but IDEA's "catch the spark" intent argues against the latency |
| 11 | Empty `/recall` query (just `/recall` with no args) | Prompt: *"What do you want to recall?"* (mirror `/capture` no-args) | Alternative: open a "recent captures" view (`Glob` with mtime sort). Defer unless asked |
| 12 | Flag typo handling (`type:decsion`) | Error: *"unknown type: decsion. Valid: idea, exploration, decision, session, thread, task, meeting."* | If typos are frequent, add fuzzy-match suggestion |

Items 1, 2, 4 are the most likely to move based on real use. Items 7, 9, 10 are stable defaults unlikely to revisit pre-1.0.

---

## Verification (Phase A acceptance)

Lifted from the plan; recorded here so the implementation PR's Test plan section can copy-paste.

- Smoke-test `/capture` end-to-end in a project repo (freeform DECISION) — note lands in `.notes/decisions/<slug>.md`, pre-linked to any matching prior decisions.
- Smoke-test `/capture` from the personal vault (`cd ~/notes/{{PERSONAL_VAULT}}` then `/capture idea: …`) — note lands in the personal vault, no pre-link (IDEA path).
- Smoke-test `/capture` with a freeform paste that contains attendees + a decision — MEETING-shape handoff fires, `/capture` declines to write, suggests `/meeting-sync`.
- Smoke-test `/recall` freeform — single-result auto-include works; multi-result list groups cleanly.
- Smoke-test `/recall scope:both jwt` — two archivist calls fire in parallel, results group by vault.
- Smoke-test `/recall type:decision since:2026-04-01` — filters applied; non-matching results excluded.
- Smoke-test `/recall attendees:bryan` — only MEETING notes with bryan in attendees return.
- Verify namespaced forms — `/cairn-notes:capture`, `/cairn-notes:recall` — auto-register correctly. No `commands/*.md` shim files present.
- CI passes (frontmatter-lint, version-check, docs-lint).

---

## Out of scope (v0.6.0 → defer to v0.7+)

- `/capture` SESSION-of-current-chat — capture the current conversation transcript as a SESSION note. Needs harness-transcript access; not a trivial extension.
- Vault-cross-project capture — "I'm in project X but want to capture about project Y" from one invocation. Today: `cd` first. v0.7+ may add a `vault:` flag on `/capture` mirroring `/recall scope:`.
- `/recall --include-working` — expose `.notes/.agents/` working files in results. Defer until a use case surfaces; today's `scope: published` default is the right v1 conservative choice.
- `/recall` natural-language `since:` — `last week`, `yesterday`. ISO-only for v0.6.0.
- `/recall` cross-project — recall across every project vault under `~/notes/*/`. Defer; today's `scope:both` (current + personal) is the maximum cardinality.
- `#cairn` brand tag on captured notes — no brand tag. If brand recognition becomes useful later, add then.
- `@athena` muscle-memory soft-landing — none. Release-note migration signal lives in Phase B's PR body, not in `/capture`.

---

## References

- Plan file (not in repo): `~/.claude/plans/she-is-scaffolding-inside-iterative-flamingo.md` — Phase A section
- Tracking issue: [#86](https://github.com/SnowboardTechie/cairn-notes/issues/86)
- Phase 0.5 PR (merged): [#87](https://github.com/SnowboardTechie/cairn-notes/pull/87)
- [archivist.md](../plugins/cairn-notes/agents/archivist.md) — extension target
- [scribe.md](../plugins/cairn-notes/agents/scribe.md) — `/capture` dispatch target
- [cairn-notes/SKILL.md](../plugins/cairn-notes/skills/cairn-notes/SKILL.md) — note templates `/capture` defers to
- [meeting-sync/SKILL.md](../plugins/cairn-notes/skills/meeting-sync/SKILL.md) — MEETING-handoff target and the precedent for "parallel archivist then scribe with resolved wikilinks"
- [issue-create/SKILL.md](../plugins/cairn-notes/skills/issue-create/SKILL.md) — repo voice and skill structure reference
- [AGENTS.md](../plugins/cairn-notes/AGENTS.md) — `commands/` vs auto-registration rules, positive-prompt conventions, vault-routing rules
