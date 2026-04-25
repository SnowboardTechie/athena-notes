---
name: issue-create
description: Draft a GitHub/Forgejo issue from a rough idea via Q&A, then post it. Triggers on "help me write an issue for…", "file an issue", "capture this as a ticket", "turn this into an issue", "write this up as an issue", or `/issue-create`.
---

# Issue Create

Turn a rough idea into a well-structured, template-faithful GitHub or Forgejo issue through four stages: **Detect → Q&A → Draft → Post**. The user reviews and approves before anything is posted.

Pairs with `issue-work` — after a successful post, the skill offers to hand off the new issue URL to `issue-work` so you can start implementation immediately.

---

## Stage 1 — Detect context

### 1.1 Resolve the target repo

```bash
remote_url=$(git remote get-url origin 2>/dev/null)
if [[ "$remote_url" == *"github.com"* ]]; then
  forge="github"
elif [[ "$remote_url" == *"forgejo"* || "$remote_url" == *"gitea"* || "$remote_url" == *"codeberg"* || "$remote_url" == *"snowboardtechie"* ]]; then
  forge="forgejo"
else
  forge="unknown"
fi
```

Branch on the result:

- **Unambiguous remote** (single origin, recognized forge) → use it.
- **Not in a repo / multi-remote / unknown forge** → ask the user which repo to file against. Accept `{owner}/{repo}` shorthand or a full URL.
- **User's initial message references a different repo** than cwd — ask before assuming. The ticket belongs wherever the idea lives, not necessarily wherever they're currently typing.

Parse `owner` and `repo` from the chosen remote:

```bash
# SSH: git@github.com:owner/repo.git → owner/repo
# HTTPS: https://github.com/owner/repo.git → owner/repo
owner_repo=$(echo "$remote_url" | sed -E 's|.*[:/]([^/]+/[^/]+?)(\.git)?$|\1|')
```

### 1.2 Scan for issue templates

**GitHub:**

```bash
# YAML form templates (new style)
Glob(pattern=".github/ISSUE_TEMPLATE/*.yml")
Glob(pattern=".github/ISSUE_TEMPLATE/*.yaml")

# Legacy Markdown templates
Glob(pattern=".github/ISSUE_TEMPLATE/*.md")
```

**Forgejo / Gitea / Codeberg:**

```bash
Glob(pattern=".forgejo/issue_template/*.md")
Glob(pattern=".gitea/issue_template/*.md")
```

Three cases:

1. **No templates found** → propose the default structure (see 1.3). Skip template-field fidelity and GraphQL issue-type steps.
2. **Exactly one template** → use it.
3. **Multiple templates** → `AskUserQuestion` with each template's `name` field as the option label. Let the user pick.

### 1.3 Default structure (no templates)

When the target repo has no `ISSUE_TEMPLATE` directory, propose this six-section structure and use it as if it were a legacy Markdown template:

```markdown
## Problem / Motivation

{problem framing from Stage 2}

## Proposed behavior

{what the user wants to happen}

## Scope

### In scope

- {item}

### Out of scope

- {item}

## Implementation hints

{constraints, relevant files, risks from Stage 2}

## Acceptance criteria

- [ ] {testable item}
- [ ] {testable item}

## Open questions

- {item}
```

Anchor: this mirrors the structure of well-written tickets the user writes by hand — problem → proposal → scope → hints → acceptance → open questions.

### 1.4 Parse the template

For GitHub YAML form templates (`.github/ISSUE_TEMPLATE/*.yml`):

```yaml
# Fields in a form template
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug"]
type: Bug                       # optional — maps to GitHub issue-type
body:
  - type: textarea
    id: summary
    attributes:
      label: Summary            # verbatim — becomes `### Summary` in the posted body
      description: ...
    validations:
      required: true
  - type: dropdown
    attributes:
      label: Severity
      options: [Low, Medium, High]
  - type: checkboxes
    attributes:
      label: Affected platforms
      options:
        - label: Linux
        - label: macOS
```

Extract:
- `title:` prefix (if present) — pre-fills the title Q&A
- `labels:` — auto-applied on post
- `type:` — if present, triggers the GraphQL `updateIssueIssueType` step in Stage 4
- Each `body:` field's `attributes.label` — used as the `### {label}` heading (verbatim casing) in the posted body

For legacy Markdown templates (`.github/ISSUE_TEMPLATE/*.md`):
- Read frontmatter (`title:`, `labels:`, `type:`) — same pre-fill behavior
- The body is plain Markdown; preserve its structure in the draft

For Forgejo templates: same as legacy Markdown. Forgejo has no issue-type field, so `type:` is ignored even if present.

---

## Stage 2 — Clarifying Q&A

### 2.1 Four open-ended areas

Ask via conversational turns (open-ended answer space). Use the user's initial framing as the seed — if they already answered an area, skip the question.

1. **Problem & motivation.** What pain/gap does this address? Who feels it? Why now?
2. **Desired outcome.** What does "done" look like from the outside? User-visible behavior? Acceptance criteria?
3. **Scope boundaries.** What's explicitly in scope vs. deferred/out-of-scope? Any non-goals worth calling out?
4. **Implementation hints.** Known constraints, likely files/components touched, alternatives considered, risks.

Match answers to template fields by label. If the template has a field that none of the answers cover, ask an additional targeted question. If the template has a field that's already covered by an answer, don't re-ask.

### 2.2 Metadata collection

#### Labels

```bash
# GitHub — name-only is enough; gh issue create takes labels by name
gh label list --repo {owner}/{repo} --json name --limit 100

# Forgejo — keep id alongside name; the POST body wants integer IDs
tea api "/repos/{owner}/{repo}/labels" | jq '[.[] | {id, name}]'
```

If the list is empty, silently skip.

On the Forgejo path, after the user picks label names, map each back to its integer id for Stage 4.2's `labels` payload field. Milestones work the same way — Forgejo expects `milestone: {id}` (integer), so capture the milestone's `id` from the API response, not just the title.

Use `AskUserQuestion` with `multiSelect: true`. Include a "none" option and a free-text "other" option.

**Pre-check label suggestions based on the Stage 2 answers before presenting the question.** The template's `labels:` field (if any) always pre-checks. On top of that, infer from the draft's content using these signals — they apply to any repo's label set, so match by name substring (case-insensitive):

| Signal from Q&A | Label name contains | Rationale |
|---|---|---|
| Scope is one file or a handful of lines; no cross-cutting concerns; no new abstractions; implementation hints fit in a sentence | `quick win`, `easy`, `low-hanging` | Small, self-contained — catch these so they're findable later when you want a focused session |
| Only changes files under `docs/`, `README`, or `*.md` | `docs`, `documentation` | Pure documentation change |
| Proposes or adds a new skill (mentions `SKILL.md`, skill directory, new capability) | `new-skill` | Matches this plugin's convention |
| User-visible new behavior, not a fix | `feature`, `enhancement` | Pick whichever exists; prefer `feature` if both |
| Existing behavior is broken / regresses | `bug` | Unambiguous |
| Body needs external input before implementation is scoped | `question`, `help wanted` | Pick `question` if it exists, else `help wanted` |

Do **not** pre-check `good first issue` from a "this is small" signal alone — that label has external discoverability semantics (newcomer search on GitHub) and should only be used when the issue is genuinely suitable for a first-time contributor to the repo. Leave it for the user to add manually.

Pre-checked labels still go through `AskUserQuestion` — the user sees them as checked defaults and can uncheck any that miss.

#### Milestone

```bash
# GitHub — title is enough; gh issue create --milestone takes a title
gh api "repos/{owner}/{repo}/milestones?state=open" --jq '[.[] | .title]'

# Forgejo — keep id alongside title; the POST body wants an integer id
tea api "/repos/{owner}/{repo}/milestones?state=open" | jq '[.[] | {id, title}]'
```

If the list is empty, silently skip.

Use `AskUserQuestion` single-select with "(none)" as a default option. On the Forgejo path, after the user picks a title, look up its `id` from the response above for Stage 4.2's `milestone` payload field.

#### Project (GitHub only)

Forgejo has no Projects equivalent — skip this subsection entirely on the Forgejo path.

Query Projects **linked to this repo** (not the owner-scoped list, which surfaces boards unrelated to this repo). Pass `owner` / `name` as GraphQL variables rather than inlining them into the query body — matches the variable-binding form used by the issue-type queries in Stage 4.3/4.4:

```bash
gh api graphql -f query='
  query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
      projectsV2(first: 20) {
        nodes { title closed }
      }
    }
  }' \
  -f owner="$owner" -f name="$repo" \
  --jq '[.data.repository.projectsV2.nodes[] | select(.closed == false) | .title]'
```

If the query itself fails (non-zero exit, error in response) — most commonly missing `project` scope or a transient API error — surface the error and ask: *"The GitHub Projects query failed ({error}). If this is a scope error, re-auth with `gh auth refresh -s project` and re-run me. Otherwise, continue posting without attaching to a project? [yes / stop]"*. Treat silence or any non-`yes` reply as stop. Do not silently fall through to the zero-projects branch; that looks identical to "this repo has no linked projects" and quietly drops the attachment.

Branch on a successful response:

- **Zero open linked projects** → skip silently. No prompt, no flag.
- **Exactly one open linked project** → attach it automatically. One linked project is unambiguous, so no prompt. Capture the title for Stage 4.2's `--project` flag.
- **Two or more open linked projects** → `AskUserQuestion` single-select with each title plus `(none)`. Capture the selection (empty when `(none)`).

### 2.3 Parent linkage (GitHub only)

Forgejo has no native sub-issue concept — skip this entire subsection silently on the Forgejo path. The flow continues to Stage 3 with `parent` empty in the draft frontmatter.

**Always prompt.** Even when the candidate set is empty, ask the user in 2.3.4 — never silently skip. Some issues legitimately have no parent, but that's the user's call.

#### 2.3.1 Build the candidate set

**Why two arrays.** Seed `#N` references go into `direct_parents[]` and become parent options directly in 2.3.4. Label-cluster siblings go into `siblings[]` and feed the convergence inference in 2.3.3 (their `parent` field is what we infer from). The two sources behave differently from 2.3.3 onward; keep them separate, then take their union for the single batched query in 2.3.2.

The batched GraphQL query in 2.3.2 interpolates these numbers directly into the alias list, so every value entering `direct_parents[]` or `siblings[]` must match `^[1-9][0-9]*$` — a strict positive-integer guard, no leading zeros, `0` excluded since GitHub issues start at 1. Apply the guard at the source for each loop:

1. **Seed `#N` references → `direct_parents[]`.** Scan the user's initial framing and Q&A answers for bare `#N` patterns (drop cross-repo `{owner}/{repo}#N` references — this skill only links within the target repo). The capture group must be the integer only; trailing characters from a loose regex would survive into the alias list. When someone says "follow-up to #656" the natural reading is that *#656 is the parent* — surface these directly as parent options in 2.3.4 rather than treating them as siblings to infer a parent from.

   ```bash
   direct_parents=()
   while read -r n; do
     [[ "$n" =~ ^[1-9][0-9]*$ ]] && direct_parents+=("$n")
   done < <(printf '%s\n' "$user_seed_text" | grep -oE '(^|[^/A-Za-z0-9_-])#[0-9]+' | grep -oE '[0-9]+')
   ```

2. **Label-cluster siblings → `siblings[]`.** Open issues in the target repo that share **all** selected labels (full intersection). Skipped if no labels were selected in 2.2 — full-intersection on zero labels matches every open issue, which is noise. The `gh issue list --json number` output is already integer-typed, but the same regex guard applies on the way in:

   ```bash
   search_terms=""
   for l in "${selected_labels[@]}"; do
     search_terms+=" label:\"$l\""
   done
   search_terms="${search_terms# }"

   siblings=()
   while read -r n; do
     [[ "$n" =~ ^[1-9][0-9]*$ ]] && siblings+=("$n")
   done < <(gh issue list \
     --repo "$owner/$repo" \
     --state open \
     --search "$search_terms" \
     --limit 20 \
     --json number \
     --jq '.[].number')
   ```

Build the de-duplicated, capped query set. Order matters — `direct_parents[]` entries kept first so a heavy label cluster can't crowd out user-named numbers, then `siblings[]` filling the remaining slots up to a total of 20:

```bash
candidates=()
for n in "${direct_parents[@]}" "${siblings[@]}"; do
  # Skip if already added (dedup). Without this, a number in both arrays would
  # produce duplicate GraphQL aliases (`i123:` twice) and the API rejects the
  # whole batch with a parse error.
  for existing in "${candidates[@]}"; do
    [[ "$existing" == "$n" ]] && continue 2
  done
  candidates+=("$n")
  (( ${#candidates[@]} >= 20 )) && break
done
```

If `candidates` is empty → skip 2.3.2 and 2.3.3, jump to 2.3.4 (which still prompts, with only `Specify a different parent` and `No parent` available).

#### 2.3.2 Query candidates

One batched GraphQL request, one alias per candidate. Fetch each candidate's own `state` + `title` (used to render direct parents as options) and its `parent { … }` (used to derive convergence among siblings). Without `-H "GraphQL-Features: sub_issues"` the `parent` field returns `Field 'parent' doesn't exist on type 'Issue'`.

```bash
# 'i' prefix required — GraphQL alias names cannot start with a digit. Stripped in --jq via sub("^i"; "").
# Defensive re-guard: 2.3.1's source-loop validation should have caught any non-integer,
# but interpolating into a query string has zero error-recovery, so we re-check at the boundary.
aliases=""
for n in "${candidates[@]}"; do
  [[ "$n" =~ ^[1-9][0-9]*$ ]] || continue
  aliases+="i${n}: issue(number: ${n}) { number title state parent { number title state } }
"
done

gh api graphql \
  -H "GraphQL-Features: sub_issues" \
  -f query="
    query(\$owner: String!, \$repo: String!) {
      repository(owner: \$owner, name: \$repo) {
        $aliases
      }
    }
  " \
  -f owner="$owner" -f repo="$repo" \
  --jq '.data.repository | to_entries | map(select(.value != null)) | map({n: (.key | sub("^i"; "") | tonumber), self: {title: .value.title, state: .value.state}, parent: .value.parent})'
```

The `--jq` filter drops `null` issues (a bad number returns `null` rather than an error) and reshapes the rest into `[{n, self: {title, state}, parent: {number, title, state} | null}, …]`.

If the call fails (non-zero exit, error in response — most commonly the `sub_issues` preview not enabled on the account, or rate limit), surface the error and ask: *"Parent search failed ({error}). Continue without inferred-parent suggestions? [yes / stop]"*. Treat silence or any non-`yes` reply as stop. On `yes`, **fall through to 2.3.4** — the "always prompt" invariant holds even in the failure path. Since the failed query was the source of titles and states, direct parents render as bare `Link under #N` (no `{title}`, no `(closed)` indicator), inferred-parent suggestions are dropped entirely, and `Specify a different parent` + `No parent` remain available as always.

#### 2.3.3 Find convergence (siblings only)

Among candidates whose `n` is in `siblings[]` but **not** in `direct_parents[]`, tally the non-null `parent.number` values:

- **Single agreed parent** (all non-null sibling parents converge on one number) → primary inferred suggestion.
- **Mixed parents** → sort by count descending; take up to 3 distinct parents as inferred suggestions.
- **All sibling parents are `null`** → no inferred suggestions; only direct parents (if any) reach 2.3.4.

#### 2.3.4 Ask the user

Use `AskUserQuestion` single-select. Always include all of:

- **Direct parents** (one option per `direct_parents[]` entry): `Link under #N — {title}`, with ` (closed)` appended when the candidate's own `self.state == "CLOSED"` — for direct parents, `self` *is* the parent. Listed first — the user named these explicitly, so they should not have to retype them via `Specify`.
- **Inferred parents** from 2.3.3 (up to 3): same option shape, with ` (closed)` appended when the inferred parent's `parent.state == "CLOSED"` (the sibling's parent — a different object than `self`). **Drop any inferred-parent number that already appears in `direct_parents[]`** — convergence can land on a number the user named directly, and showing it twice as `Link under #N — {title}` would be visually duplicative without conveying anything new.
- `Specify a different parent` — on selection, ask a follow-up turn: *"Parent issue number? (e.g. `42`, or `skip`)"*. Validate the answer parses as a positive integer; on invalid input or `skip`, treat as `No parent`. Persist the typed number directly — Stage 4.5.3's verify step catches a non-existent or otherwise invalid parent on the post side. We deliberately don't pre-confirm or surface state at draft time; the user typed the number explicitly, and a closed-parent linkage is allowed.
- `No parent` — default. The natural choice when no candidates surfaced or the user has none in mind.

Capture the result as a single integer (parent issue number) or empty.

#### 2.3.5 Persist on the draft

In Stage 3.2's frontmatter, write `parent: {N}` (or empty when not chosen). The actual link happens in Stage 4.5 after the issue is created — at draft time we only need to remember the choice.

---

## Stage 3 — Draft & review

### 3.1 Resolve the drafts directory

Use the `agent-workspace` skill's trunk-resolution pattern:

```bash
# resolve_trunk_root is defined in agent-workspace/SKILL.md
TRUNK_ROOT=$(resolve_trunk_root)
DRAFTS_DIR="$TRUNK_ROOT/.notes/.agents/drafts"
mkdir -p "$DRAFTS_DIR"
```

If `$TRUNK_ROOT/.notes` doesn't exist yet, run the auto-setup protocol from [agent-workspace/SKILL.md](../agent-workspace/SKILL.md).

If the user chose a **target repo that differs from cwd** in Stage 1, still use cwd's `.notes/` for the draft — the draft is local-to-the-thinker, not local-to-the-issue. Record the target `{owner}/{repo}` in the draft frontmatter so future-you can trace which repo it got posted to.

### 3.2 Render the draft

File: `$DRAFTS_DIR/issue-create-<slug>-<timestamp>.md`

- `slug` = lowercased title, non-alphanumerics → `-`, collapsed, trimmed, max 40 chars
- `timestamp` = `YYYYMMDD-HHMM`

Content layout — YAML frontmatter for metadata, then the issue body sections. **The frontmatter is metadata only; it is stripped before posting.** The body-section lines are exactly what the forge will render as the issue body — no `# {title}` line (the title is a separate API field, not part of the body).

```markdown
---
kind: issue-draft
target: {owner}/{repo}
template: {template-filename or "default-structure"}
title: {chosen title}
labels: [{selected labels}]
milestone: {selected milestone or empty}
project: {selected project or empty}
parent: {parent issue number from Stage 2.3, or empty}
type: {template's type: field, or empty}
created: {iso8601}
---

## {field label 1}

{user's answer, verbatim}

## {field label 2}

{user's answer, verbatim}

...
```

**Heading fidelity rules:**

- **Legacy Markdown template OR default structure** → use `##` headings matching the template's section structure.
- **GitHub YAML form template** → use `### {label}` (three hashes) with verbatim casing from `attributes.label`. The web form renders field labels as H3, so a programmatic post must match exactly. Do not "improve" the label's casing or wording.
- **`textarea` and `input` fields** → `### {label}\n\n{user's answer}`.
- **`checkboxes` fields** → render as `- [ ] {option.label}` bullets under the `### {label}` heading.
- **`dropdown` fields** → `### {label}\n\n{selected option}`.

### 3.3 Show & iterate

Present the full draft inline. Accept conversational edits: "tighten the problem section", "add a note about X", "change the title to Y". Re-render and re-present until the user approves.

Approval is conversational — "looks good," "approve," "post it," "ship it," all count. If the user says anything ambiguous, ask explicitly: "Ready to post?"

---

## Stage 4 — Post & hand off

### 4.1 Dedup check (best-effort)

Before posting, search for similar open issues:

```bash
# GitHub — search by title keywords
title_keywords=$(echo "$title" | tr -d '[:punct:]' | head -c 100)
gh issue list --repo "$owner/$repo" --state open --search "$title_keywords" \
  --json number,title,url --limit 3

# Forgejo — per-repo issue list accepts q= for title/body substring search.
# Note the path: /repos/{owner}/{repo}/issues (NOT /issues/search — that's the
# global cross-repo endpoint). Response is a bare array.
tea api "/repos/$owner/$repo/issues?q=$(jq -rn --arg q "$title_keywords" '$q|@uri')&type=issues&state=open&limit=3" \
  | jq '[.[:3][] | {number, title, html_url}]'
```

- **Zero matches** → silently continue to 4.2.
- **One or more matches** → show them inline to the user: "Found similar open issues. Still post, or amend one of these instead?" Wait for explicit "post" before continuing. If they want to amend, stop — this skill does not edit existing issues.

### 4.2 Post the issue

**First, strip the frontmatter** from the draft. The YAML frontmatter is metadata for the drafting workflow; it must not appear in the posted issue body:

```bash
# Skip the first ---...--- block; keep everything after it.
# Only skip the leading blank line that conventionally follows the closing ---.
# A naive "skip line after the second ---" eats the first body line when the
# draft writer omits the blank separator.
BODY_FILE=$(mktemp)
awk '
  BEGIN { n = 0; started = 0 }
  !started && /^---$/ { n++; if (n <= 2) next }
  !started && n >= 2 {
    if ($0 == "") next   # eat one blank line (conventional), then start printing
    started = 1
  }
  started { print }
' "$DRAFT_PATH" > "$BODY_FILE"
```

**GitHub:**

The `--label` flag takes one label name per occurrence. Build the command so each selected label becomes its own `--label`:

```bash
# Build --label / --milestone / --project flags as arrays so values with spaces survive.
label_flags=()
for l in "${selected_labels[@]}"; do label_flags+=(--label "$l"); done

milestone_flag=()
[[ -n "$milestone" ]] && milestone_flag=(--milestone "$milestone")

project_flag=()
[[ -n "$project" ]] && project_flag=(--project "$project")

gh issue create \
  --repo "$owner/$repo" \
  --title "$title" \
  --body-file "$BODY_FILE" \
  "${label_flags[@]}" \
  "${milestone_flag[@]}" \
  "${project_flag[@]}"
```

The command prints the new issue URL on success. Capture it.

**Forgejo:**

```bash
# Extract token from tea config (pattern mirrors ship/SKILL.md)
TEA_CONFIG=""
for candidate in \
  "${XDG_CONFIG_HOME:-$HOME/.config}/tea/config.yml" \
  "$HOME/Library/Application Support/tea/config.yml" \
  "$HOME/.tea/tea.yml"; do
  [ -f "$candidate" ] && TEA_CONFIG="$candidate" && break
done
TOKEN=$(grep 'token:' "$TEA_CONFIG" | head -1 | awk '{print $2}')

instance=$(echo "$remote_url" | sed -E 's|.*(@\|//)([^:/]+).*|https://\2|')

# Labels must be resolved to integer IDs for the Forgejo API.
# Build JSON payload — env vars are exported so python3 sees them.
# TITLE / LABELS_JSON / MILESTONE_NUM come from the Q&A + label-id lookup.
export TITLE="$title"
export LABELS_JSON="${labels_id_json:-[]}"              # e.g. [3, 7]; default [] when no labels chosen
export MILESTONE_NUM="${milestone_num:-}"               # integer or empty

payload=$(python3 -c "
import json, os, sys
out = {
    'title': os.environ['TITLE'],
    'body': sys.stdin.read(),
    'labels': json.loads(os.environ['LABELS_JSON']),
}
m = os.environ.get('MILESTONE_NUM')
if m:
    out['milestone'] = int(m)
print(json.dumps(out))
" < "$BODY_FILE")

curl -s -X POST "${instance}/api/v1/repos/${owner}/${repo}/issues" \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload" \
  | jq '{number, html_url}'
```

### 4.3 Set issue type (GitHub only, when template has `type:`)

If the resolved template has a `type:` field (e.g., `type: Task`), set it via GraphQL after creation. Forgejo has no issue-type concept — skip this step for Forgejo.

#### 4.3.1 Resolve the issue-type ID

Lazy cache at `$TRUNK_ROOT/.notes/.agents/issue-create/type-ids.md`:

```markdown
---
kind: issue-type-cache
---

## owner/repo

- Task: IT_kwDOABc123
- Bug: IT_kwDOABc456
- Epic: IT_kwDOABc789

## other-owner/other-repo

- Deliverable: IT_kwDOXYZ...
```

**Read cache first.** Parse the section matching the target `{owner}/{repo}`, then find the template's `type:` name. If cached, use it.

**On cache miss**, fetch via GraphQL:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!) {
    repository(owner: $owner, name: $repo) {
      issueTypes(first: 50) {
        nodes {
          id
          name
        }
      }
    }
  }
' -f owner="$owner" -f repo="$repo" \
  | jq -r '.data.repository.issueTypes.nodes[] | "\(.name)=\(.id)"'
```

Parse output, find the ID matching the template's `type:` name (case-sensitive). Write through to the cache file, creating the section for this `{owner}/{repo}` if it doesn't exist.

If the template's `type:` name doesn't appear in `issueTypes.nodes`, stop and report: "Template specifies type `{name}` but the repo doesn't have that issue type configured. Issue was created (see URL) but type not set."

#### 4.3.2 Call the mutation

Get the new issue's node ID:

```bash
issue_node_id=$(gh api "repos/$owner/$repo/issues/$new_issue_number" --jq '.node_id')
```

Set the type:

```bash
gh api graphql -f query='
  mutation($issueId: ID!, $typeId: ID!) {
    updateIssueIssueType(input: {issueId: $issueId, issueTypeId: $typeId}) {
      issue {
        number
        issueType { id name }
      }
    }
  }
' -f issueId="$issue_node_id" -f typeId="$type_id"
```

### 4.4 Verify + retry

Re-query the issue to confirm the type is actually set:

```bash
verified_type=$(gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        issueType { name }
      }
    }
  }
' -f owner="$owner" -f repo="$repo" -F number="$new_issue_number" \
  --jq '.data.repository.issue.issueType.name // ""')
```

`gh api --jq '... // ""'` turns a JSON `null` into an empty string, so a bash `[[ -z ... ]]` test is reliable. Do not test against the literal word `null` — an issue type literally named "null" would collide (unlikely but the `// ""` pattern is unambiguous either way).

- **Non-empty** (returns a name) → success. Continue to 4.5 (Link parent).
- **Empty** → wait 2 seconds, retry the mutation from 4.3.2 once, then re-verify.
- **Still empty after retry** → report: "Issue #{N} created but type not set. Retry manually: `gh api graphql -f query='mutation { updateIssueIssueType(input: {issueId: \"$issue_node_id\", issueTypeId: \"$type_id\"}) { issue { issueType { name } } } }'`." Continue to 4.5 (Link parent) anyway — the issue exists.

### 4.5 Link parent issue (GitHub only, when `parent` set in 2.3)

Skip this stage entirely when:

- `forge == forgejo` (no native sub-issue concept), or
- The draft's `parent:` field is empty (user picked `No parent` in 2.3.4).

Otherwise, link the new issue under the chosen parent. Mirrors the 4.3+4.4 pattern: mutation, then verify, then one retry on failure.

**Read `parent_number` from the draft frontmatter before doing anything else.** On a resume path (re-invoking `/issue-create` against a saved draft), the `parent:` field is the only place the choice persists across sessions — Stage 2.3.5 wrote it; Stage 4.5 reads it. The variable name `$parent_number` referenced below assumes this assignment has happened.

#### 4.5.1 Resolve node IDs

The new issue's node ID was already resolved in 4.3.2 as `$issue_node_id`. Reuse it (resolve it here if 4.3 was skipped, e.g. no-template path):

```bash
[[ -z "$issue_node_id" ]] && issue_node_id=$(gh api "repos/$owner/$repo/issues/$new_issue_number" --jq '.node_id')
parent_node_id=$(gh api "repos/$owner/$repo/issues/$parent_number" --jq '.node_id')
```

If `parent_node_id` is empty (404 on a missing issue, or any other error — `gh` will have printed the cause to stderr), report `"Parent #$parent_number lookup failed — skipping linkage."` and continue to 4.6 (Archive) without linking. The issue exists; we'd rather skip the link with a visible reason than swallow auth/network errors as if they were "parent not found."

#### 4.5.2 Call addSubIssue

The `sub_issues` preview header is required. Without it the mutation returns `Field 'addSubIssue' doesn't exist on type 'Mutation'`.

```bash
gh api graphql \
  -H "GraphQL-Features: sub_issues" \
  -f query='
    mutation($parentId: ID!, $childId: ID!) {
      addSubIssue(input: {issueId: $parentId, subIssueId: $childId}) {
        subIssue { number }
      }
    }
  ' -f parentId="$parent_node_id" -f childId="$issue_node_id"
```

#### 4.5.3 Verify

Re-query the new issue's `parent.number` and compare against the chosen parent:

```bash
verified_parent=$(gh api graphql \
  -H "GraphQL-Features: sub_issues" \
  -f query='
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        issue(number: $number) {
          parent { number }
        }
      }
    }
  ' -f owner="$owner" -f repo="$repo" -F number="$new_issue_number" \
    --jq '.data.repository.issue.parent.number // ""')
```

`// ""` turns a JSON `null` into an empty string (same pattern as 4.4) so `[[ -z ... ]]` is reliable.

- **Matches `$parent_number`** → success. Continue to 4.6 (Archive).
- **Empty or mismatched** → wait 2 seconds, retry the mutation from 4.5.2 once, then re-verify.
- **Still wrong after retry** → report a fenced code block with the actual `$parent_node_id` / `$issue_node_id` / `$N` values **substituted inline** before display (do not show literal `{parent_node_id}` placeholders — a user copy-pasting the rendered block must get a working command). The retry uses GraphQL variable binding (same shape as 4.5.2), not query-string interpolation, so quoting is straightforward:

  ````
  Issue #<actual N> created but parent linkage to #<actual parent_number> failed. Retry manually:

      gh api graphql \
        -H 'GraphQL-Features: sub_issues' \
        -f parentId=<actual parent_node_id> \
        -f childId=<actual issue_node_id> \
        -f query='mutation($parentId: ID!, $childId: ID!) { addSubIssue(input: {issueId: $parentId, subIssueId: $childId}) { subIssue { number } } }'
  ````

  Continue to 4.6 (Archive) anyway — the issue exists.

### 4.6 Archive the draft

On successful post — i.e., the issue was created in 4.2, regardless of whether 4.3 (type-set), 4.4 (type-verify), and 4.5 (parent-link + verify) all succeeded. The issue exists; archival is unconditional once 4.2 returns a URL:

```bash
ARCHIVE_DIR="$TRUNK_ROOT/.notes/.agents/_archive/issue-create"
mkdir -p "$ARCHIVE_DIR"
DATE=$(date +%Y-%m-%d)
mv "$DRAFT_PATH" "$ARCHIVE_DIR/${DATE}-${slug}.md"
```

Append a URL footer to the archived file:

```markdown
---
Posted: {url}
```

(Three dashes after body content render as a horizontal rule. The archived file keeps the original frontmatter for retro value; the footer `---` comes after the body sections, not as a second frontmatter block.)

On **post failure** (`gh issue create` or Forgejo API failed) → draft stays in `drafts/`. Report the error and the draft path. User can retry by re-invoking `/issue-create` with the saved draft.

On **type-set failure after retry** (4.4 returned null twice) or **parent-link failure after retry** (4.5.3 still mismatched after retry) → still archive the draft, since the issue exists. Include the relevant manual-retry command in the user-facing report.

### 4.7 Report + handoff

Show the user:

```
✓ Issue created: {markdown link to url}

Labels: {applied}
Milestone: {applied or "—"}
Project: {attached or "—"}
Parent: {linked #N or "—" or "⚠ not linked, retry manually"}
Type: {set or "—" or "⚠ not set, retry manually"}

Archived draft: {archive path}
```

Then ask: "Start working on this now?" If yes, invoke the `issue-work` skill with the new issue URL. If no, stop.

---

## Edge Cases

| Case | Behavior |
|---|---|
| `cwd` isn't a git repo | Ask user for `{owner}/{repo}` |
| Multiple remotes (`origin` + `upstream`) | Default to `origin`; confirm with user |
| Target repo differs from cwd | Use cwd's `.notes/` for draft; record target in frontmatter |
| Template has `title:` prefix | Pre-fill user's title suggestion with the prefix |
| Template has required fields | Don't post with empty answers; re-ask |
| `gh auth status` fails | Stop. Tell user to `gh auth login` |
| Forgejo token missing | Stop. Tell user token source (tea config) |
| No labels / no milestones in repo | Skip the `AskUserQuestion` prompts silently |
| User edits draft mid-Stage 3 | Re-render from user's edits; continue iteration |
| User says "actually, let me think more" | Leave draft in `drafts/`; exit cleanly; re-invoke later picks up by listing drafts |
| Dedup check finds identical title | Surface + ask — never auto-merge |
| GraphQL rate-limited | Surface the rate-reset time from the response header; don't loop |
| `sub_issues` preview disabled on the account | Stage 2.3.2 surfaces the error; ask `[yes / stop]` to continue without parent linkage |
| Parent number user typed (`Specify a different parent`) is invalid (non-integer, `skip`, or empty) | Treat as `No parent` silently; `parent:` stays empty in the draft |
| Confirmed parent number is valid at draft time but doesn't exist (or is inaccessible) at post time | Stage 4.5.1 reports `"Parent #N lookup failed — skipping linkage."` and continues to 4.6; the issue still posts |
| Convergence picks a closed parent | Offer it with `(closed)` in the option label; user decides |
| User picks a parent in 2.3 but post fails in 4.2 | Draft retains `parent:` in frontmatter; re-invoking `/issue-create` resumes with the choice intact |

---

## Things This Skill Does NOT Do

- **Edit existing issues.** (Separate skill if wanted.)
- **Post to multiple repos at once.**
- **Auto-link parent or related issues without confirmation.** Stage 2.3 always asks before linking; user can pick `No parent`. Free-text `#N` references in the body are preserved as-is, never auto-converted into linkages.
- **Bulk-create issues from a list.**
- **Assign anyone other than the default (caller is author, no assignees).**
- **Add `Co-authored-by: Claude` trailers** to the issue body.
- **Auto-delete drafts** — archiving on success is the cleanup step; pyre handles the archive directory later if the user wants.
- **Retry failed posts silently.** Errors surface to the user; they decide whether to retry.

---

## Related

- [issue-work/SKILL.md](../issue-work/SKILL.md) — the implementation half; offered as a handoff after successful post
- [agent-workspace/SKILL.md](../agent-workspace/SKILL.md) — drafts directory conventions + trunk resolution + archive pattern
- [ship/SKILL.md](../ship/SKILL.md) — source of the forge-detection pattern reused here
