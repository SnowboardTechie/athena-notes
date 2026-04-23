# Triage UI

Per-finding decision prompt shape used by `pr-self-review` Phase 2.3.

---

## Per-finding mode (default when unsuppressed findings ≤ 5)

Use `AskUserQuestion` per finding. Question carries the finding text and related context; options are fixed.

```
Question: {lens} • {file}:{line}
  {finding text}

  Related issue:  #{N} — {title} ({url})
  Related note:   [[{wikilink}]] ({note_type}) — {1-line summary}

Options (single-select):
  1. accept           — Claude edits the code; you eyeball the diff at end of pass
  2. push-back <...>  — you give a one-line rationale; suppressed for rest of session
  3. issue            — hand off to /issue-create (dedup checks related-issues + repo)
  4. skip             — drop silently for this session
```

Options are stable across findings — always these four. When a `related_issue` or `related_note` line is present on the finding, **pre-select `skip`** and annotate the label: `skip (related to #{N})` or `skip (settled in [[wikilink]])`.

The `push-back` action requires a rationale. Implement it as: if the user picks `push-back`, follow up with a single-line free-text prompt: "Why?". Record the rationale keyed to the finding.

---

## Batch mode (fallback when unsuppressed findings > 5)

Running 12 `AskUserQuestion` prompts in a row is obnoxious. Switch to a single batched prompt.

Render the findings as a numbered list, group by severity (Critical → Major → Minor → Nit), and show related context inline. End with a single free-text prompt where the user replies with one action per line, in the shorthand:

```
Findings this pass:

[Critical]
  1. correctness | src/auth/login.ts:42
     Empty-string username bypasses the rate-limit check — rate-limiter keys on
     `user.id ?? username` which becomes "" for unregistered requests and shares
     the same bucket across all anonymous traffic.

[Major]
  2. security | src/api/upload.ts:88
     Unvalidated `Content-Type` echoed back in error body — potential XSS if
     an attacker supplies a crafted MIME string.
     ↳ related_issue: #47 "Sanitize error responses"

  3. simplicity | src/utils/format.ts:12
     Three-line wrapper around Intl.NumberFormat with no caller-specific logic —
     drop it; let callers use Intl directly.

[Nit]
  4. simplicity | src/components/Header.tsx:3
     Unused import: `useMemo`.
     ↳ related_note: [[decision-header-memoization]] (decision) — Memoization intentionally deferred in v1

Reply with one line per finding:

  {num} accept
  {num} push-back <reason>
  {num} issue
  {num} skip

Findings you don't mention are treated as skip.
```

Parse the reply; apply in order. If the user writes `push-back` with no rationale, re-prompt for that line only (do not re-present the full batch).

---

## Suppression key

A single finding's identity across passes is the tuple `{lens}|{file}|{line}|{sha8(message)}`, where:

- `lens` is the reviewer lens (`correctness` / `security` / `simplicity`).
- `file` is the repo-relative path the reviewer cited.
- `line` is the line number the reviewer cited; if the reviewer gave a range (`42-48`), use the first number.
- `sha8(message)` is the first 8 hex chars of SHA-256 of the finding text, **normalized** by lowercasing + collapsing runs of whitespace into a single space + stripping leading/trailing whitespace. This tolerates pure whitespace/casing drift between passes while still catching reworded findings.

Why this shape: path + line + hash is enough to distinguish most findings in practice; whitespace normalization avoids a spurious non-match when a reviewer reformats its own prose between passes; the lens prefix prevents a `simplicity` skip from accidentally masking a later `correctness` catch on the same line.

---

## Session state layout (in-memory only, never persisted)

```
suppression_set: Set<string>          # suppression keys
pushbacks: List<{key, reason}>        # for summary.md reporting
filed_issues: List<{key, url}>        # to auto-suppress on re-surface
skips: List<key>                      # for summary.md reporting
accepts_per_pass: List<List<{key, file, line, lens, summary}>>
pass_count: int
```

All of this dies when the skill run ends. `~/.claude/pr-self-review/.../` only holds the JSON caches and the final `summary.md` / `review-{lens}.md` files — the decision log is a report of what the user picked, not an input to future runs.
