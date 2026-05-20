---
name: recall
description: Search the vault for notes matching a freeform query. Optional flags filter by scope (project/personal/both), type, date, or attendees. Single matches auto-include the note body; multi-match groups by vault. Triggers on `/recall <query>` or `/recall <flags> <query>`.
---

# Recall

The primary user-facing retrieval surface. Search the vault for notes matching a freeform query and optional filters, with a single archivist call (one vault) or two parallel calls (both vaults).

Pairs with [`/capture`](../capture/SKILL.md) — the natural capture counterpart.

---

## Quick Reference

```
/recall <query>                               # search the current vault
/recall scope:both <query>                    # search both project and personal vaults
/recall type:decision <query>                 # filter by note type
/recall since:2026-04-01 <query>              # filter by date (frontmatter date: >= this)
/recall attendees:alice,bob <query>           # filter MEETING notes by attendee (intersection)
/recall scope:personal type:decision <query>  # flags can combine; order doesn't matter
```

All flags are optional. The query is the trailing text after the last `key:value` pair.

---

## Philosophy

Recall is `archivist` with a user-friendly entry shape. The skill itself is mostly flag parsing and result formatting; the actual search is the archivist's job. Three principles fall out:

- **Defer to archivist.** This skill never duplicates search strategies, frontmatter parsing, or note reading. It composes the right archivist prompt and presents what comes back.
- **Default to the current vault.** If you're in a project repo, `/recall` searches the project vault. If you're in `~/notes/{{PERSONAL_VAULT}}/`, it searches there. `scope:both` is the explicit opt-in for cross-vault.
- **Group by vault.** When `scope:both` returns matches from both vaults, group results visibly. Readers track their current scope by the source they're reading from; interleaving destroys that signal.

---

## Workflow

### Step 1: Parse the args

Pull leading `key:value` flags from the args. Any of:

- `scope:project` | `scope:personal` | `scope:both`
- `type:idea` | `type:exploration` | `type:decision` | `type:session` | `type:thread` | `type:task` | `type:meeting`
- `since:YYYY-MM-DD`
- `attendees:name1,name2,...`

Match the regex `^(?:[a-z]+:[^\s]+\s+)*` against the start of args. Each `key:value` pair is consumed; the remainder is the query. Flags can appear in any order; each flag at most once.

If no flags are present, the entire args string is the query.

If the args are empty (`/recall` with nothing after), prompt:

> *"What do you want to recall?"*

Use the user's reply as the args and re-parse.

**Cross-flag validation** (after parsing, before dispatch):

- `attendees:` is meeting-only. If `attendees:` is present alongside `type:` where `type:` ≠ `meeting`, stop with: *"`attendees:` only applies to MEETING notes. Drop `type:{value}` or change it to `type:meeting`."*
- Same flag passed twice → stop with: *"Each flag can appear at most once. Got `{flag}:` twice."*
- `type:` / `since:` / `attendees:` value validation fails → stop with the specific error from the [Edge cases](#edge-cases) table.

Cross-flag validation runs *before* scope resolution so the user sees the error before any archivist call.

See [`references/query-shapes.md`](references/query-shapes.md) for the flag-translation rules — how each flag becomes part of the archivist prompt — and for the parsing edge cases (whitespace in values, colons in values, etc.).

### Step 2: Resolve scope

Determine which vault(s) to search.

**Default scope** depends on `cwd` and mirrors [`scribe`](../../agents/scribe.md#notes-path-resolution)'s three-mode detection so retrieval reaches the same vault that capture would write to:

- **Project mode** — cwd is inside a git repo (with or without a `.notes/` symlink) → default `scope:project`.
- **Direct vault mode** — cwd is inside `{notes_root}/<vault>/` (any vault directory under `notes_root`, not just `{{PERSONAL_VAULT}}`) → default `scope:<absolute-path-to-that-vault>`. Parse `notes_root` from `~/.claude/cairn/identity.md`. This handles the user who `cd`s into `~/notes/another-project/` to work in that vault directly.
- **Default mode** — anywhere else → default `scope:personal`.

The flag overrides the default. Resolved scopes:

| Resolved scope | Archivist calls |
|---|---|
| `project` | One call with `vault: project` (or no `vault:` line — same effect) |
| `personal` | One call with `vault: personal` |
| `<absolute-path>` (Direct vault default only — not user-facing as a flag in v0.6.0) | One call with `vault: <absolute-path>` |
| `both` | Two parallel calls in one assistant turn — one with `vault: project`, one with `vault: personal` |

`scope:both` and the Direct-vault default both depend on the [archivist `vault:` extension](../../agents/archivist.md#vault) added in this same release.

Out of scope for v0.6.0: a user-facing `scope:<path>` flag, or `scope:all` across every `{notes_root}/*` vault. Direct-vault recall happens implicitly when cwd lands in that vault. The deferred `scope:` extensions are a v0.7+ follow-up.

### Step 3: Dispatch archivist

Build the archivist prompt(s) per the resolved scope.

#### Single-vault call (scope:project, scope:personal, or Direct vault default)

```
Task(subagent_type="archivist", prompt="vault: {project|personal|<absolute-path>}
scope: published

Find notes about: {query}.

{If type: flag was passed:}
Filter to notes whose frontmatter contains 'type: {value}'.

{If since: flag was passed:}
Filter to notes whose frontmatter 'date:' field is on or after {YYYY-MM-DD}.

{If attendees: flag was passed:}
Filter to MEETING notes whose 'attendees:' frontmatter list includes ALL of: {comma-separated names}.

Return up to 10 matches with type, wikilink, path, and a 1-line summary. If exactly one match, include the full note body verbatim after the summary.")
```

`scope: published` is always sent — `.notes/.agents/` working files are excluded. `--include-working` to expose drafts is a deferred follow-up.

If `vault:` is `project`, omit the `vault:` line entirely (it's the archivist default; sending it adds noise without changing behavior).

The "if exactly one match, include the full note body" instruction triggers the single-result auto-include. Archivist already reads candidate files via the Read tool, so adding the body to its response is a small additional step.

#### Multi-vault call (scope:both)

Fire two archivist calls in **parallel** — one assistant turn, two Task tool uses in the same message:

```
# In one message:
Task(subagent_type="archivist", prompt="vault: project
scope: published

Find notes about: {query}.
{filters as above}
Return up to 10 matches with type, wikilink, path, and a 1-line summary. If exactly one match, include the full note body.")

Task(subagent_type="archivist", prompt="vault: personal
scope: published

Find notes about: {query}.
{filters as above}
Return up to 10 matches with type, wikilink, path, and a 1-line summary. If exactly one match, include the full note body.")
```

The two calls run concurrently. Both responses are then merged in Step 4. Do not interleave results across vaults — group by source.

For the single-result auto-include rule with `scope:both`: include the body only when the *total* match count across both vaults is 1. If each vault returns 1 match (total 2), present both as a list without bodies — the user can re-invoke with the slug if they want a body.

### Step 4: Format and present

See [`references/result-formatting.md`](references/result-formatting.md) for the three result-shape branches with worked examples.

Quick summary:

**Zero results:**

```
No matches for "{query}" in {vault(s)}.

{Suggestions: try broader terms, check spelling, or `/capture` to record this as a new topic.}
```

For `scope:both`, name both vaults so the user knows the breadth: `"No matches for "{query}" in project or personal vaults."`

**Single result** (one match across all searched vaults):

```
1 match in {vault}:

[[slug]] — {type} — {path}
{1-line summary}

---

{full note body verbatim}
```

**Multi-result** (more than one match):

```
{N} matches in {vault}:

1. [[slug-a]] — decision — {path}
   {1-line summary}

2. [[slug-b]] — exploration — {path}
   {1-line summary}

...
```

For `scope:both` multi-result, present each vault as its own section with a heading. Do not interleave.

After a multi-result list, do NOT prompt for "pick a number to view the body." The user re-invokes with a more specific query (or the slug) if they want a body. Cleaner re-entry, less stateful UX.

---

## Edge cases

| Case | Behavior |
|---|---|
| Empty query (just `/recall` with no args after prompt) | Re-prompt once: *"Query can't be empty — what should I search for?"* Second empty → stop with `"Recall cancelled (no query)."` |
| `type:` value not in the known seven types (e.g., `type:decsion`) | Stop with: *"Unknown note type: `{value}`. Valid: idea, exploration, decision, session, thread, task, meeting."* No archivist call. |
| `since:` value isn't ISO date `YYYY-MM-DD` | Stop with: *"`since:` requires ISO date `YYYY-MM-DD`. Got `{input}`."* Natural-language dates (`last week`, `yesterday`) are out of scope for v0.6.0. |
| `attendees:` with one or more names containing special characters | Pass the raw value to archivist — it does a frontmatter match against the YAML `attendees:` list, where Bryan's notes can contain any string. Quoting is the archivist's problem. |
| `scope:both` when `~/.claude/cairn/identity.md` is missing or `personal_vault:` unset | The personal-vault archivist call returns the "personal vault not configured" error. Present that as a partial result in Step 4: project-vault results still show, plus a one-line `ⓘ Personal vault not configured — run /cairn-setup to enable.` Do not fail the whole recall — project results are still useful. |
| `scope:project` from outside a git repo | Stop with: *"`scope:project` requires a git repo. Run from inside a project, or use `scope:personal`."* |
| Direct vault default — cwd is `{notes_root}/<vault>/` but `<vault>` is the personal vault | Treat as Project's sibling — resolve to `vault: <absolute-path>` so the search hits that vault directly. (Equivalent to `vault: personal` in practice, but the absolute-path form skips the identity-file lookup; behavior is identical.) |
| Direct vault default — `~/.claude/cairn/identity.md` missing, so `notes_root` can't be parsed | Fall back to Default mode (`scope:personal` with the `~/notes/` default), and surface the missing-identity message in the response. Don't fail recall — the user gets results from somewhere reasonable. |
| One vault returns results, the other returns zero (scope:both) | Show the populated vault's results normally; under a second heading, show `"No matches in {other-vault}."` Don't suppress the empty section — the user wants to know the absence is real, not a bug. |
| Archivist times out or errors on one of two parallel calls | Show the successful call's results; under a heading for the failed vault, show `"⚠ {vault} search failed: {error}."` Don't fail the whole recall. |
| Single result has no `date:` frontmatter and a `since:` filter was active | Archivist's filter excludes it. The user gets a "no results" response. If this turns out to be common (many older notes lack `date:`), revisit by making `since:` skip filtering when the field is missing. |

---

## Guardrails

- Do NOT search `.notes/.agents/` working files — always send `scope: published` to archivist.
- Do NOT interleave results across vaults under `scope:both` — group by source with a heading per vault.
- Do NOT prompt the user to "pick a number" after a multi-result list. Let them re-invoke with the slug if they want body inline.
- Do NOT accept non-ISO `since:` values. Reject with a clear error; ISO-only is the v0.6.0 contract.
- Do NOT extend `scope:` beyond `project | personal | both`. Cross-project recall (`~/notes/*` aggregate) is a deferred follow-up.
- Do NOT fall back to default behavior when an unknown flag value is passed. Stop with a clear error so the user can re-issue correctly.
- Do NOT cache or persist results. Each `/recall` invocation is a fresh archivist call; staleness isn't a category here.

---

## Related

- [`archivist`](../../agents/archivist.md) — the search engine this skill dispatches to; see *Vault* and *Scope* for the directive shapes
- [`capture`](../capture/SKILL.md) — the capture counterpart; suggests `/capture` in the zero-results message
- [`cairn-notes`](../cairn-notes/SKILL.md) — note-type definitions used by the `type:` filter
