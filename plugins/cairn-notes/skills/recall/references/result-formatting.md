# Result formatting — three branches with worked examples

Loaded by [`/recall`](../SKILL.md) Step 4 when assembling the user-facing response. The branch is determined by the total match count across all searched vaults.

---

## Zero results

When all dispatched archivist calls return zero matches.

### Single-vault

```
No matches for "{query}" in {project|personal} vault.

Try broader terms or check spelling. If this is a new topic worth recording, run `/capture` to seed a note.
```

### Multi-vault (scope:both)

```
No matches for "{query}" in project or personal vaults.

Try broader terms or check spelling. If this is a new topic worth recording, run `/capture` to seed a note.
```

The `/capture` suggestion is intentional — recall and capture pair up. Zero results often means "this isn't recorded yet" and capture is the right next move.

---

## Single result (total across all searched vaults = 1)

When the total match count across all dispatched archivist calls is exactly 1, include the full note body.

### Single-vault, one match

Archivist returns one match plus the full body (per the prompt's "if exactly one match, include the full note body verbatim" instruction).

```
1 match in {project|personal} vault:

[[decision-default-model]] — decision — `.notes/decisions/default-model-sonnet-4-6.md`

> Switched default model from Haiku 4.5 to Sonnet 4.6 due to CI rate-limit hits.

---

{full note body verbatim, including frontmatter}
```

The path is rendered as a clickable markdown link to the file. The 1-line summary lives in a blockquote so it visually separates from the body.

### Multi-vault (scope:both), one match total

Same shape, but the vault label names which vault returned the match:

```
1 match in personal vault (0 in project):

[[decision-default-model]] — decision — `~/notes/second-brain/decisions/default-model-sonnet-4-6.md`

> Switched default model from Haiku 4.5 to Sonnet 4.6 due to CI rate-limit hits.

---

{full note body verbatim}
```

The "(0 in project)" annotation makes the absence visible — the user knows the other vault was actually searched, not skipped.

---

## Multi-result (total across all searched vaults > 1)

When the total match count exceeds 1, present a list. Do not include note bodies — the user re-invokes with a more specific query (or the slug) if they want a body.

### Single-vault, multi-match

```
{N} matches in {project|personal} vault:

1. [[slug-a]] — decision — `.notes/decisions/slug-a.md`
   {1-line summary}

2. [[slug-b]] — exploration — `.notes/explorations/slug-b.md`
   {1-line summary}

3. [[slug-c]] — task — `.notes/tasks/slug-c.md`
   {1-line summary}

...up to 10 matches.
```

Number each match (1, 2, 3...) so the user has a visual ordering. The wikilink is the canonical handle; the path is the clickable file link.

### Multi-vault (scope:both), multi-match

Group by vault under a section heading per vault. Do not interleave.

```
## Project vault ({N} matches)

1. [[slug-a]] — decision — `.notes/decisions/slug-a.md`
   {1-line summary}

2. [[slug-b]] — exploration — `.notes/explorations/slug-b.md`
   {1-line summary}

## Personal vault ({M} matches)

1. [[slug-c]] — idea — `~/notes/second-brain/ideas/slug-c.md`
   {1-line summary}

2. [[slug-d]] — decision — `~/notes/second-brain/decisions/slug-d.md`
   {1-line summary}
```

The section headings make the vault boundary unmissable. Renumbering restarts per vault (each vault has its own `1, 2, 3`); a global numbering would suggest a global ordering that doesn't actually exist (the two archivist calls don't share a relevance comparator).

### One vault empty, the other populated (scope:both)

Show the populated vault's results normally; show the empty vault's section explicitly:

```
## Project vault ({N} matches)

1. [[slug-a]] — decision — ...

## Personal vault

No matches.
```

Don't suppress the empty section. The user wants to know the absence is real.

### One vault errored (scope:both)

Show the successful vault normally; show the failed vault's error under a section heading:

```
## Project vault ({N} matches)

1. [[slug-a]] — decision — ...

## Personal vault

⚠ Search failed: vault not accessible — personal vault not configured (run /cairn-setup).
```

Partial results are still useful. The user gets to see what was findable and a clear pointer to what blocked the rest.

---

## Worked example: `/recall scope:both default model`

User invokes from inside a project repo:

```
/recall scope:both default model
```

Step 1 — Parse args. Flag: `scope:both`. Query: `default model`.

Step 2 — Resolve scope. `scope:both` → two parallel archivist calls.

Step 3 — Dispatch. One assistant turn, two Task tool uses in the same message.

Archivist responses:
- Project vault: 1 match (`decision-default-model`).
- Personal vault: 1 match (`exploration-model-economics`).

Step 4 — Format. Total match count = 2 (one per vault). This is multi-result, not single-result, so no bodies are included.

```
## Project vault (1 match)

1. [[decision-default-model]] — decision — `.notes/decisions/default-model-sonnet-4-6.md`
   Switched default model from Haiku 4.5 to Sonnet 4.6 due to CI rate-limit hits.

## Personal vault (1 match)

1. [[exploration-model-economics]] — exploration — `~/notes/second-brain/explorations/model-economics.md`
   Comparing Sonnet 4.6 / Opus 4.7 / Haiku 4.5 cost-per-token for different workload shapes.
```

The user can re-invoke `/recall decision-default-model` (or the wikilink slug) to get the body of either match.
