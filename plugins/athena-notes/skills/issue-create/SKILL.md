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

### 2.2 Metadata via `AskUserQuestion`

#### Labels

```bash
# GitHub
gh label list --repo {owner}/{repo} --json name --limit 100

# Forgejo
tea api "/repos/{owner}/{repo}/labels" | jq '[.[] | .name]'
```

If the list is empty, silently skip.

Use `AskUserQuestion` with `multiSelect: true`. Include a "none" option and a free-text "other" option.

#### Milestone

```bash
# GitHub
gh api "repos/{owner}/{repo}/milestones?state=open" --jq '[.[] | .title]'

# Forgejo
tea api "/repos/{owner}/{repo}/milestones?state=open" | jq '[.[] | .title]'
```

If the list is empty, silently skip.

Use `AskUserQuestion` single-select with "(none)" as a default option.

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

Content:

```markdown
---
kind: issue-draft
target: {owner}/{repo}
template: {template-filename or "default-structure"}
title: {chosen title}
labels: [{selected labels}]
milestone: {selected milestone or empty}
type: {template's type: field, or empty}
created: {iso8601}
---

# {title}

## {field label 1}

{user's answer, verbatim}

## {field label 2}

{user's answer, verbatim}

...
```

**Heading fidelity rules:**

- **Legacy Markdown template OR default structure** → use `##` headings matching the template's section structure.
- **GitHub YAML form template** → use `### {label}` (three hashes) with verbatim casing from `attributes.label`. The web form renders field labels as H3, so a programmatic post must match exactly. Do not "improve" the label's casing or wording.
- **Checkboxes from a form template** → render as `- [ ] {option.label}` bullets.
- **Dropdowns** → `### {label}\n\n{selected option}`.

### 3.3 Show & iterate

Present the full draft inline. Accept conversational edits: "tighten the problem section", "add a note about X", "change the title to Y". Re-render and re-present until the user approves.

Approval is conversational — "looks good," "approve," "post it," "ship it," all count. If the user says anything ambiguous, ask explicitly: "Ready to post?"

---

## Stage 4 — Post & hand off

### 4.1 Dedup check (best-effort)

Before posting, search for similar open issues:

```bash
# GitHub — search by title keywords
title_keywords=$(echo "$title" | tr -d '[:punct:]' | tr ' ' ' ' | head -c 100)
gh issue list --repo "$owner/$repo" --state open --search "$title_keywords" \
  --json number,title,url --limit 3

# Forgejo
tea api "/repos/$owner/$repo/issues/search?q=$(jq -rn --arg q "$title_keywords" '$q|@uri')&type=issues&state=open" \
  | jq '.data[:3] | [.[] | {number, title, html_url}]'
```

- **Zero matches** → silently continue to 4.2.
- **One or more matches** → show them inline to the user: "Found similar open issues. Still post, or amend one of these instead?" Wait for explicit "post" before continuing. If they want to amend, stop — this skill does not edit existing issues.

### 4.2 Post the issue

**GitHub:**

```bash
gh issue create \
  --repo "$owner/$repo" \
  --title "$title" \
  --body-file "$DRAFT_PATH" \
  --label "$labels_comma_joined" \
  $([ -n "$milestone" ] && echo "--milestone \"$milestone\"")
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

# Build JSON payload — use python3 for safe escaping
body_content=$(cat "$DRAFT_PATH")
payload=$(python3 -c "import json,sys,os; \
  print(json.dumps({'title': os.environ['T'], 'body': sys.stdin.read(), 'labels': json.loads(os.environ['L']), 'milestone': int(os.environ['M']) if os.environ.get('M') else None}))" \
  <<< "$body_content")

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
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      issue(number: $number) {
        issueType { name }
      }
    }
  }
' -f owner="$owner" -f repo="$repo" -F number="$new_issue_number" \
  --jq '.data.repository.issue.issueType.name'
```

- **Non-null** (returns a name) → success. Continue to 4.5.
- **Null** → wait 2 seconds, retry the mutation from 4.3.2 once, then re-verify.
- **Still null after retry** → report: "Issue #{N} created but type not set. Retry manually: `gh api graphql -f query='mutation { updateIssueIssueType(input: {issueId: \"$issue_node_id\", issueTypeId: \"$type_id\"}) { issue { issueType { name } } } }'`." Continue to 4.5 anyway — the issue exists.

### 4.5 Archive the draft

On successful post (type set or type not needed — i.e., Forgejo, no-template, or verified non-null after 4.4):

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

(Two dashes is intentional — a minimal horizontal rule, not a new frontmatter block.)

On **post failure** (`gh issue create` or Forgejo API failed) → draft stays in `drafts/`. Report the error and the draft path. User can retry by re-invoking `/issue-create` with the saved draft.

On **type-set failure after retry** (4.4 returned null twice) → still archive the draft, since the issue exists. Include the manual-retry command in the user-facing report.

### 4.6 Report + handoff

Show the user:

```
✓ Issue created: {markdown link to url}

Labels: {applied}
Milestone: {applied or "—"}
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

---

## Things This Skill Does NOT Do

- **Edit existing issues.** (Separate skill if wanted.)
- **Post to multiple repos at once.**
- **Auto-link related issues/PRs.** (User can reference them in their answers — the draft preserves whatever they write.)
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
