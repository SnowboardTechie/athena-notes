# Query shapes — flag → archivist-prompt translation

Loaded by [`/recall`](../SKILL.md) Step 3 when composing the archivist prompt. This reference is the single place where flag semantics are defined; adding a new flag to `/recall` means adding a row here.

---

## `scope:` — vault selection

| Flag | Resolves to | Archivist directive |
|---|---|---|
| `scope:project` | current repo's trunk `.notes/` | omit `vault:` line (archivist default) |
| `scope:personal` | `~/notes/{{PERSONAL_VAULT}}/` from `~/.claude/cairn/identity.md` | `vault: personal` |
| `scope:both` | both | two parallel calls — one with `vault: project` (or omitted), one with `vault: personal` |

If `scope:` is absent, the default depends on `cwd` (see [SKILL.md Step 2](../SKILL.md#step-2-resolve-scope)).

---

## `type:` — note-type filter

| Flag | Archivist prompt addition |
|---|---|
| `type:idea` | `Filter to notes whose frontmatter contains 'type: idea'.` |
| `type:exploration` | `Filter to notes whose frontmatter contains 'type: exploration'.` |
| `type:decision` | `Filter to notes whose frontmatter contains 'type: decision'.` |
| `type:session` | `Filter to notes whose frontmatter contains 'type: session'.` |
| `type:thread` | `Filter to notes whose frontmatter contains 'type: thread'.` |
| `type:task` | `Filter to notes whose frontmatter contains 'type: task'.` |
| `type:meeting` | `Filter to notes whose frontmatter contains 'type: meeting'.` |

Validation: the value must match one of the seven known types exactly (case-insensitive). On unknown values, stop with the error from [SKILL.md Edge cases](../SKILL.md#edge-cases) — do not pass through.

The archivist's [Strategy 1: Frontmatter search](../../../agents/archivist.md#strategy-1-frontmatter-search) already greps for these patterns; the filter is implemented agent-side.

---

## `since:` — date filter

| Flag | Archivist prompt addition |
|---|---|
| `since:YYYY-MM-DD` | `Filter to notes whose frontmatter 'date:' field is on or after {YYYY-MM-DD}.` |

Validation: the value must match the regex `^\d{4}-\d{2}-\d{2}$` (basic ISO date — no time component, no timezone). On invalid values, stop with the error from [SKILL.md Edge cases](../SKILL.md#edge-cases).

Natural-language dates (`last week`, `yesterday`, `Q1`) are out of scope for v0.6.0. ISO-only is the contract. If natural-language dates become a frequent ask, add a small parser; ISO stays the canonical form.

**Notes without a `date:` field.** Archivist's filter excludes them when `since:` is active. Most cairn-notes templates include `date:` in frontmatter (per [`cairn-notes/SKILL.md`](../../cairn-notes/SKILL.md)), so this is rare. If it becomes a recurring miss, revisit by making `since:` skip filtering when the field is missing rather than excluding the note.

---

## `attendees:` — meeting-attendee filter

| Flag | Archivist prompt addition |
|---|---|
| `attendees:name` | `Filter to MEETING notes whose 'attendees:' frontmatter list includes 'name'. Also implies type: meeting.` |
| `attendees:name1,name2` | `Filter to MEETING notes whose 'attendees:' frontmatter list includes ALL of: name1, name2. Also implies type: meeting.` |

Validation: split the value on `,` and trim whitespace from each name. No type-checking on the names themselves — frontmatter attendees can be any string.

**Names with spaces are not supported in v0.6.0.** The flag-parsing regex `^(?:[a-z]+:[^\s]+\s+)*` treats whitespace as a flag separator, so `attendees:Alice Smith,Bob` would parse as `attendees:Alice` plus `Smith,Bob` falling into the query. Use a single-token form per attendee (`attendees:alice,bob`). Quoted-value support is a v0.7+ follow-up.

**Matching is case-insensitive.** Archivist folds both the filter value and the frontmatter `attendees:` value to lowercase before comparing (per the [Filters section in archivist.md](../../../agents/archivist.md#filters)). `attendees:alice` matches frontmatter `Alice`, `ALICE`, or `alice`.

**Allowed characters.** Tokens must match `[A-Za-z0-9._-]+`. Punctuation (quotes, apostrophes, backticks, etc.) is rejected up-front per the [Edge cases](../SKILL.md#edge-cases) table — keeps the filter clause from carrying ambiguous characters into archivist's natural-language interpretation.

`attendees:` implies `type:meeting`. If the user passes both `attendees:` and `type:` where `type:` is not `meeting`, stop with: *"`attendees:` only applies to MEETING notes. Drop `type:{value}` or change it to `type:meeting`."*

Multi-name intersection — `attendees:bryan,alice` returns meetings where *both* attended, not either-or. Union/either-of is a deferred follow-up.

---

## Combining flags

Flags can be combined in any order. The archivist prompt accumulates a filter clause per flag, AND-ed together. Example invocation:

```
/recall scope:both type:decision since:2026-04-01 default model
```

Translates to two parallel archivist calls, each with:

```
scope: published

Find notes about: default model.

Filter to notes whose frontmatter contains 'type: decision'.

Filter to notes whose frontmatter 'date:' field is on or after 2026-04-01.

Return up to 10 matches with type, wikilink, path, and a 1-line summary. If exactly one match, include the full note body.
```

(The first call adds `vault: project` — actually omits it, since project is the archivist default; the second call adds `vault: personal`.)

---

## Flag-value parsing edge cases

| Case | Behavior |
|---|---|
| Same flag passed twice (`type:decision type:idea`) | Stop with: *"Each flag can appear at most once. Got `type:` twice."* The user can re-issue with a single flag. |
| Flag value contains a colon (`since:2026-04-01T00:00:00`) | The regex greedy-matches up to whitespace, so the whole value is the value. ISO date validation then rejects it as not matching `^\d{4}-\d{2}-\d{2}$`. Tell the user: ISO date only, no time component. |
| Trailing flag with no value (`scope: project` — note space) | The regex requires no whitespace inside `key:value`. Treat `scope:` as an unrecognized token (no value, so `value=""` which fails validation). Stop with: *"Flag value can't be empty."* |
| Query before flags (`default model scope:both`) | The flag-parsing regex is anchored at start. A `key:value` in the middle of the query is treated as part of the query, passed to archivist as a literal phrase. This is intentional: `/recall code:1234 the error` should search for the literal text `code:1234 the error`. |
