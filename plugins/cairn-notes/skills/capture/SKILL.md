---
name: capture
description: Capture a thought, decision, exploration, or other note directly into the vault. Auto-detects the note type, optionally pre-links related prior notes, and delegates writing to scribe. Triggers on `/capture <text>` (freeform), `/capture <type>:<text>` (explicit prefix — idea, exploration, decision, session, thread, task, meeting), or `/capture` with no args (interactive).
---

# Capture

The primary user-facing capture surface. Turn a thought, decision, or exploration into a durable note without manual file-system navigation. `/capture` classifies intent, dispatches `scribe` for the write, and (for DECISION / EXPLORATION) pre-links related prior notes via `archivist`.

Pairs with [`/recall`](../recall/SKILL.md) — the natural retrieval counterpart.

---

## Quick Reference

```
/capture <text>                   # auto-detect type from the body
/capture <type>: <text>           # force the type (idea, exploration, decision, session, thread, task, meeting)
/capture                          # interactive — prompt for the body, then auto-detect
```

`<type>` is one of: `idea`, `exploration`, `decision`, `session`, `thread`, `task`, `meeting`. Case-insensitive. The `meeting:` prefix triggers the [MEETING handoff](#step-4-meeting-shape-handoff) — `/meeting-sync` is the correct surface for meeting routing.

---

## Philosophy

Capture is the lowest-friction op in the cairn-notes system. The job is to remove the steps between "I had a thought" and "the thought is durably in the vault." Three principles fall out of that:

- **Trust the heuristic.** Type detection is good enough most of the time. When it isn't, ask once, not twice.
- **Defer to existing infrastructure.** [`scribe`](../../agents/scribe.md) handles vault routing, folder selection, filename slugging, and template application. This skill never duplicates that logic.
- **Pre-link where it pays.** DECISION and EXPLORATION captures benefit from being linked to prior thinking; IDEA and TASK captures don't. Linking everything would buy latency for little value.

---

## Workflow

### Step 1: Resolve the input form

Inspect the args to `/capture`:

- **Empty args** → no-args interactive. Prompt:
  > *"What do you want to capture?"*

  Read the user's reply as the body. Treat it as a freeform input for the rest of the workflow.

- **Args start with `<type>:`** → explicit-prefix. Match `^\s*(idea|exploration|decision|session|thread|task|meeting)\s*:\s*` case-insensitive against the args. On match: strip the prefix, force the named type, **skip Step 2 (detection)**, and proceed to Step 4 if `meeting`, otherwise Step 5.

- **Otherwise** → freeform. The full args are the body. Proceed to Step 2.

### Step 2: Detect the type

For freeform inputs, classify the body into one of the seven note types by inspecting it for signals. See [`references/type-detection.md`](references/type-detection.md) for the signal table and worked examples.

The detector returns a `(type, confidence)` tuple where confidence is `high`, `medium`, or `low`:

- **`high`** — at least one strong signal *and* shape match. Skip Step 3; proceed to Step 4.
- **`medium`** — one signal, ambiguity between two types. Run Step 3 with the top 2 candidates.
- **`low`** — no strong signals, or competing signals across types. Run Step 3 with the top 3 candidates.

If the detector returns MEETING (at any confidence), proceed to Step 4 — the MEETING handoff fires regardless of confidence.

### Step 3: Confidence-gate (medium / low only)

Use `AskUserQuestion` to confirm the type. Frame positively (per [`AGENTS.md` → "Positive prompts for approval gates"](../../AGENTS.md#positive-prompts-for-approval-gates)):

> Question: *"This looks like {primary}{ or {secondary}}. Which type should it be?"*
> Header: `Note type`
> Options:
> - `{primary}` (e.g., `Decision`)
> - `{secondary}` (e.g., `Exploration`)
> - `{tertiary}` (low-confidence only — third candidate)

The `AskUserQuestion` tool auto-provides an "Other" option for free-form input. If the user picks `Other` and types a value, validate it against the seven known types; on an unknown value, re-ask once.

Once the user picks, treat that as the confirmed type and proceed to Step 4 (or Step 5 if not MEETING).

See [`references/interactive-flow.md`](references/interactive-flow.md) for the full gate dialogue patterns including edge cases.

### Step 4: MEETING-shape handoff

If the resolved type is **MEETING** (from explicit prefix `meeting:` or from detection matching the [meeting-sync shape check](../meeting-sync/SKILL.md#shape-check)), `/capture` does not write directly. Meetings produce an anchor plus spin-offs — the right surface is [`/meeting-sync`](../meeting-sync/SKILL.md).

Present:

> This looks like meeting notes (attendees / decisions / action items detected). The `/meeting-sync` skill routes meeting blobs into a MEETING anchor plus DECISION / TASK / IDEA spin-offs. Want to switch over?
>
> *[switch to /meeting-sync / capture as a single SESSION note anyway / abort]*

Branch on the reply:

- **switch to /meeting-sync** → respond with: *"Run `/meeting-sync` and paste the same text. The skill will walk you through the anchor + spin-offs."* Stop. Do not chain into the meeting-sync skill from inside `/capture`; nested slash-command invocation is awkward in Claude Code and the re-entry is the user's natural next step.
- **capture as a single SESSION note anyway** → fall back to the SESSION path. Force the type to SESSION, skip Step 5 (no pre-link for SESSION), proceed to Step 6 with the body intact.
- **abort** → stop without writing. Report `"Capture aborted."`

Treat silence or ambiguity as a re-prompt, not as approval.

### Step 5: Pre-link via archivist (DECISION + EXPLORATION only)

For **DECISION** and **EXPLORATION** captures, dispatch `archivist` first, **await its response**, then proceed to Step 6 with the wikilinks inlined into the scribe prompt. The two calls are sequential by force — scribe's prompt has a data dependency on archivist's output, so they can't run in parallel even though both go through `Task`. The pre-link surfaces relevant prior notes so the new capture lands with its lineage attached.

For **IDEA / TASK / SESSION / THREAD**, skip this step entirely (go straight to Step 6). Speed > linkage:
- IDEA — the point is catching the spark; an extra hop adds latency.
- TASK — linkage usually sits in the ticket id (in the body or filename), not in cross-references.
- SESSION — user-initiated summary; user names the links if they want.
- THREAD — meta-note that explicitly enumerates its connected notes.

Archivist call shape:

```
Task(subagent_type="archivist", prompt="scope: published

Find notes related to this capture: {2-3 sentence summary of the body, drawn from its strongest topical keywords}. Return up to 5 wikilinks with one-line relevance notes.")
```

`scope: published` excludes `.notes/.agents/` working files. No `vault:` directive — archivist falls through to its trunk-root protocol, so **pre-link only fires in project-vault captures** (cwd inside a git repo). Personal-vault and Direct-vault captures proceed without a pre-link in v0.6.0 — archivist would fail with "not in a git repository" and `/capture` would skip the `Related notes:` line per the failure-path rule below. Multi-vault and personal-vault pre-linking are deferred follow-ups.

Archivist's response yields up to 5 wikilink candidates. Take the top 3 most relevant and inline them into the scribe prompt (Step 6).

**On archivist failure or empty result.** Drop the `Related notes:` line from the scribe prompt entirely. Don't write "Related notes: (none found)" — that's noise in the note body. If archivist returned an error (vault inaccessible, malformed response), note the failure in the Step 7 user-facing summary; the capture still proceeds.

The two calls are sequential — scribe's prompt depends on archivist's wikilinks. (Unlike [`meeting-sync`](../meeting-sync/SKILL.md)'s archivist↔archivist parallelism, which works because the two archivist calls are independent.)

### Step 6: Dispatch scribe

Compose the scribe Task call:

```
Task(subagent_type="scribe", prompt="Write {TYPE} note. Body:

{captured text}

{If Step 5 yielded matches: Related notes: [[slug-a]], [[slug-b]], [[slug-c]]}")
```

Trust scribe's handling — no explicit vault path, no folder selection override, no filename argument. Scribe applies its three-mode vault resolution (Project / Direct vault / Default per [`scribe.md`](../../agents/scribe.md)), its Note Reuse Protocol (update over duplicate), its folder selection (existing project structure or cairn defaults), and the appropriate template from the [`cairn-notes`](../cairn-notes/SKILL.md) reference skill.

`/capture` only forwards `(type, body, related_links)`. Match meeting-sync's pattern: trust scribe's resolution. To target the personal vault from inside a project repo, `cd ~/notes/{{PERSONAL_VAULT}}` first.

### Step 7: Report

After scribe returns its `Wrote: {relative_path}` line, present to the user.

**Validate before rendering.** If `{relative_path}` contains a `..` segment or starts with `/`, do *not* render it as a clickable link — display the path as plain text and surface the anomaly to the user. Scribe should never emit a path with traversal, but the assertion costs nothing and prevents a hyperlink that clicks through to an unexpected location.

**Path prefixing.** Scribe's `{relative_path}` is *vault-relative* (e.g., `decisions/foo.md`), not cwd-relative. For the clickable link to resolve from the user's terminal, prefix it to match the resolution mode scribe used:

| Cwd state when `/capture` was invoked | Link href |
|---|---|
| Inside a project repo (cwd or trunk has a `.notes/` symlink) | `.notes/{relative_path}` |
| Inside `~/notes/<vault>/` (Direct vault mode) | `{relative_path}` (cwd already is the vault root) |
| Anywhere else (Default mode — scribe wrote to the personal vault) | The absolute path scribe expanded `~/notes/<personal_vault>/{relative_path}` to; if you don't know it, fall back to `{relative_path}` |

Detect mode with `Bash(command="git rev-parse --path-format=absolute --git-common-dir")` (the same single-command shape archivist's Startup uses — see [`archivist.md`](../../agents/archivist.md#startup-resolve-vault-root)), then `Glob` for `.notes/` under that trunk path to confirm the vault symlink. From a worktree, `--show-toplevel` would return the worktree root and miss the trunk-only `.notes/` symlink; `--git-common-dir` correctly resolves to the trunk. Cache the resolution; mode doesn't change inside one capture turn.

Then present:

```
✓ Captured as {TYPE}: [{relative_path}]({prefixed_href})

{1-2 line summary of what was written, derived from scribe's response}

{If Step 5 ran and yielded links:
→ Linked: [[slug-a]], [[slug-b]], [[slug-c]]}

{If Step 5 ran but failed or empty:
ⓘ No related notes pre-linked.}
```

The display text stays `{relative_path}` so the user sees the canonical vault-relative shape; only the href is prefixed for click-through. No `Co-Authored-By:` trailers.

See [`references/examples.md`](references/examples.md) for four end-to-end worked captures showing the report shape for each branch.

---

## Edge cases

| Case | Behavior |
|---|---|
| Empty body (no-args, user replies with whitespace) | Re-prompt: *"Capture body can't be empty — paste the thought, or send `abort` to stop."* |
| Explicit-prefix `<type>:` with unknown type (e.g., `/capture decsion:`) | Treat as freeform — the prefix didn't match the regex. Detection runs on the full body including the typo. |
| Multiple `:` characters in the body (e.g., `/capture decision: chose X: rationale was Y`) | The regex only consumes the *first* `<type>:` prefix. The rest of the body, including subsequent colons, is captured verbatim. |
| User picks `Other` in the Step 3 gate and types an unknown type | Re-ask once. Second unknown value → fall back to the detector's primary candidate and proceed; report the fallback in Step 7. |
| Archivist returns valid results but none feel relevant | Pass the top 3 to scribe regardless. Filtering "relevant enough" is the user's job — they can edit the note after. |
| Scribe reports a Note Reuse update (existing note matched) | Step 7 reports `"Updated existing note"` instead of `"Captured as"`. The path link still applies. |
| Cwd is not in a git repo and `~/notes/{{PERSONAL_VAULT}}/` doesn't exist | Scribe auto-creates the personal vault on first write and reports the setup. `/capture` surfaces scribe's setup message in Step 7. |
| User sends `/capture` then immediately Ctrl-C before answering the no-args prompt | No writes happened. No cleanup needed. |
| MEETING-shape detected but user picks `capture as a single SESSION note anyway` | SESSION's pre-link rule applies — no archivist call. The full body (including attendee list, decisions, action items) lands in one SESSION note. Suboptimal but honors the override. |

---

## Guardrails

- Do NOT duplicate the note templates from [`cairn-notes/SKILL.md`](../cairn-notes/SKILL.md). Scribe loads them; `/capture` defers.
- Do NOT pass an explicit vault path to scribe. Trust the three-mode detection.
- Do NOT chain into `/meeting-sync` inline. Report the handoff and stop; the user re-invokes.
- Do NOT block on the archivist pre-link if it fails. Capture is the priority; linkage is best-effort.
- Do NOT prompt for confirmation before scribe writes. Scribe is the only writer; `/capture` only gates on type ambiguity (Step 3) and on the MEETING handoff (Step 4).

---

## Related

- [`scribe`](../../agents/scribe.md) — the writer this skill dispatches to
- [`archivist`](../../agents/archivist.md) — pre-link source (Step 5)
- [`cairn-notes`](../cairn-notes/SKILL.md) — note templates (loaded by scribe, not by this skill)
- [`meeting-sync`](../meeting-sync/SKILL.md) — the MEETING-shape handoff target (Step 4)
- [`recall`](../recall/SKILL.md) — the retrieval counterpart
