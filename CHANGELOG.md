# Changelog

All notable changes to Athena Notes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `archivist` agent — resolves the trunk root via `git rev-parse --path-format=absolute --git-common-dir` before searching, so `.notes/` lookups succeed when the agent is invoked from a worktree. Resolves [#59](https://github.com/SnowboardTechie/athena-notes/issues/59).
- `archivist` agent — vault-existence error path now specifies a `Glob` check rather than leaving the verification mechanism implicit; placeholder syntax switched from `$TRUNK_ROOT` to `{TRUNK_ROOT}` to match `agent-workspace`. Follow-up to [#59](https://github.com/SnowboardTechie/athena-notes/issues/59).
- `issue-work` skill — Phase 1.6 worktree creation now branches off `origin/$DEFAULT_BRANCH` regardless of the session's current HEAD, via a `git worktree add` against `{TRUNK_ROOT}` followed by `EnterWorktree(path: ...)`. Resolves [#61](https://github.com/SnowboardTechie/athena-notes/issues/61).

### Added
- `core/` directory established with [`core/AGENTS.md`](core/AGENTS.md) defining the host-agnostic / host-specific boundary and the rule for where new content goes; `CONTRIBUTING.md`, `README.md`, and `plugins/athena-notes/AGENTS.md` gain forward-pointers. Resolves [#14](https://github.com/SnowboardTechie/athena-notes/issues/14).

### Changed
- `AGENTS.md` — adds rule under "When to add a new spoke" preferring a sibling skill over extending an existing spoke when an adjacent reasoning-shape match would otherwise warrant spoke shape.
- `issue-create` skill — searches for a candidate parent issue before posting and links the new issue under it when the user confirms; Forgejo path skips silently. Resolves [#47](https://github.com/SnowboardTechie/athena-notes/issues/47).
- `issue-create` skill — adds a collaborative open-questions resolution pass between draft render and approval, and removes the post-create "Start working on this now?" prompt. Resolves [#70](https://github.com/SnowboardTechie/athena-notes/issues/70).
- `workday-planning` skill — Phase 8 now opens with a persistence receipt: `✅ Wrote: …` on a fresh write, `⏭️ Kept existing: …` when the user declines to overwrite. Resolves [#30](https://github.com/SnowboardTechie/athena-notes/issues/30).
- `session-review` skill — adds a collaboration lens that routes cross-project user-preference signal (how the user thinks, project motivation, external-system pointers) to the harness memory system instead of the vault. Resolves [#13](https://github.com/SnowboardTechie/athena-notes/issues/13).

## [0.4.3] — 2026-04-23

### Changed
- `AGENTS.md` — new **Command files vs. skill auto-registration** subsection under Skill Authoring. Codifies when to add a `commands/<name>.md` file alongside a skill (full implementation, differently-named alias) and when not to (same-name shim). Surfaced in [#49](https://github.com/SnowboardTechie/athena-notes/pull/49).
- `session-review` skill — now scans today's daily plan for tracked items resolved in the session and proposes in-place edits at the approval gate. Resolves [#51](https://github.com/SnowboardTechie/athena-notes/issues/51).

## [0.4.2] — 2026-04-23

### Removed
- `plugins/athena-notes/commands/issue-create.md` and `plugins/athena-notes/commands/pr-self-review.md` — redundant command-file shims that collided with their same-named skills and broke bare-form `/issue-create` and `/pr-self-review`. Both names now resolve via skill auto-registration (bare and `/athena-notes:<name>` forms).

### Changed
- `ship` skill — preamble now states the skill's scope explicitly (WIP draft-PR shipping; self-review and merge-readiness are not its job) and points at `/issue-work` for end-to-end ticket work and `/pr-self-review` for standalone review on an already-shipped branch. The draft-PR default was already encoded in behavior; this surfaces the intent for agents and readers encountering `ship` in isolation.
- `issue-create` skill — Stage 2.2 label step now pre-checks suggested labels based on the Stage 2 answers, using name-substring matching (`quick win`/`easy`/`low-hanging`, `docs`/`documentation`, `new-skill`, `feature`/`enhancement`, `bug`, `question`/`help wanted`). Pre-checks still go through `AskUserQuestion` so the user can uncheck any that miss. `good first issue` is explicitly excluded from auto-suggestion because it carries external-discoverability semantics on GitHub.

## [0.4.1] — 2026-04-23

### Changed
- `issue-create` skill — new issues are now attached to open GitHub Projects linked to the target repo. Auto-attaches when exactly one linked project exists, prompts when more than one, skips silently when none. Forgejo path is unchanged (no Projects equivalent).

## [0.4.0] — 2026-04-22

### Added
- `pr-self-review` skill (`plugins/athena-notes/skills/pr-self-review/`) and `/pr-self-review` slash command — iterative self-review loop for PRs the user authored. Three entry points: `/pr-self-review <pr-url>`, `/pr-self-review` (infers PR from current branch), and invocation from `issue-work` Phase 4 on a pre-PR branch. Each pass pre-fetches related open issues (linked-to-PR ∪ path-touching ∪ `tech-debt`/`known-issue`/`follow-up`-labeled) and related `.notes/` entries (parallel `@archivist` calls keyed by diff topics), feeds both caches to three parallel `impl-reviewer` agents, then walks each unsuppressed finding through `accept` / `push-back <reason>` / `issue` / `skip` with per-pass commit-and-push. Findings tagged with a `related_issue` or `related_note` default to `skip` with the reference shown as rationale. Session state (push-backs, skips, filed-issue URLs) is in-memory only; caches live at `~/.claude/pr-self-review/{owner}-{repo}-{pr-or-branch}/` (standalone) or the caller's `~/.claude/issue-work/{owner}-{repo}-{N}/` (pre-pr). Repos without `.notes/` silently skip the archivist phase. Refuses on a dirty tree; refuses on PRs the user didn't author. Resolves [#9](https://github.com/SnowboardTechie/athena-notes/issues/9).
- `issue-work` Phase 4 — delegates to `/pr-self-review` in `pre-pr` mode instead of spawning three `impl-reviewer` agents inline. Same `review-{lens}.md` + `summary.md` output in the existing state dir, so Phase 4.3's ship gate keeps working unchanged — but Phase 4 now carries related-context awareness and an accept/push-back/issue/skip triage loop, so easy nits clear in-pass instead of piling into a post-merge list.
- `impl-reviewer` agent — accepts two new optional inputs (`related_issues_path` / `related_notes_path`). When a finding overlaps a cached issue or note, appends a `related_issue: #N` or `related_note: [[ref]]` line under the finding; missing or empty caches are a no-op and the output shape stays stable for callers that don't pass caches. Adds an input-path guard (every path must resolve under `~/.claude/`) and a data-not-instruction guardrail on cache content.
- `weekly-planning` skill promoted from `examples/skills/` to `plugins/athena-notes/skills/weekly-planning/` as a first-class plugin skill. `workday-planning` references `/weekly-planning` three times as the Monday depth-flow; before this migration anyone who installed the plugin without copying the example skill hit a dead reference. Vault paths now resolve from `~/.claude/athena/identity.md` with fallback defaults (`~/notes`, `second-brain`) instead of hardcoded `~/notes/second-brain/` — matches the `workday-planning` pattern. Output folder reads from a new nested `weekly_planning.output_folder` key in the existing `~/.claude/athena/planning-sources.md` (default `Journal`) instead of standing up a second per-user config file. Phase 7's output structure is embedded inline, so users no longer need a template file in their vault. Resolves [#39](https://github.com/SnowboardTechie/athena-notes/issues/39).
- `.github/workflows/frontmatter-lint.yml` and `scripts/lint-frontmatter.py` — CI lint that validates every agent (`name`/`description`/`tools`/`model`) and skill (`name`/`description`) frontmatter block, catches the OpenCode-shape `tools:` list vs. Claude Code comma-separated string, enforces the `model:` enum (`opus`/`sonnet`/`haiku`/`inherit`), and checks that skill references in main-tree agent/skill bodies resolve to real skill directories. Examples tree is validated for frontmatter but not for cross-refs (examples point at user-project skills). Runs on `pull_request` and `push` to `main`. Resolves [#1](https://github.com/SnowboardTechie/athena-notes/issues/1).
- `meeting-sync` skill (`plugins/athena-notes/skills/meeting-sync/`) — routes pasted meeting notes into a MEETING anchor plus linked DECISION / TASK / IDEA spin-offs. Mirrors `session-review`'s pattern: shape-check the paste, parse attendees/decisions/actions/ideas/open-questions, run parallel `@archivist` calls (`scope: published`) to find prior art on each topic, draft the anchor plus spin-offs plus update-proposals inline, hold an all/none/subset approval gate, then dispatch `@scribe` concurrently for approved items. Both anchor and spin-offs follow scribe's default vault routing (project `.notes/` in a repo, else personal vault). v1 is paste-only — no Granola/Otter MCP integration, no multi-vault archivist search. Resolves [#8](https://github.com/SnowboardTechie/athena-notes/issues/8).
- `athena-notes` skill — adds 7th note type **MEETING** (`YYYY-MM-DD-meeting-{slug}.md`) with frontmatter (`type`, `date`, `attendees`, `tags`, `source`) and sections for Attendees / Context / Decisions / Action Items / Open Questions / Ideas Captured / Raw Notes (collapsed). Capture Triggers table and internal-prompt list extended with the new type. Produced by `meeting-sync`; spin-offs from meetings use the existing DECISION / TASK / IDEA types.

### Changed
- `AGENTS.md` — new **Shared config: preserve foreign keys** subsection under "Skill Authoring → Per-user config vs per-project state vs plugin-local." Codifies the contract that a skill owning a `~/.claude/athena/*.md` file must preserve top-level frontmatter keys it doesn't own when a sibling skill extends the file with a nested key. Surfaced via `/session-review` after [#40](https://github.com/SnowboardTechie/athena-notes/pull/40); the pattern it documents is already implemented in `workday-planning/SKILL.md` Bootstrap Flow Step 0.
- `workday-planning` skill — Bootstrap Flow now has a Step 0 that reads the existing `planning-sources.md` (if present) and preserves every top-level frontmatter key the skill doesn't own (anything other than `output_folder` and `projects`). Previously the bootstrap wrote the file from scratch and silently dropped sibling-skill keys such as `weekly_planning:` — a user who customized `weekly_planning.output_folder` and later ran `/plan-workday --edit-sources` would lose the key with no warning. Surfaced while landing [#39](https://github.com/SnowboardTechie/athena-notes/issues/39).
- `forge` agent — accepts an optional `Output path:` prompt-prefix parameter in Task invocations. Absent value preserves the existing `.notes/.agents/forge/today.md` default write; an absolute path redirects the daily-plan write there (parent dir must exist); the literal `return-only` suppresses the write so callers that own the canonical file get goal-list text back without the side effect. Archive (`sessions/`) and `wins.md` are unaffected. Replaces the prompt-level "return goals as text only, don't write to today.md" hack `workday-planning` was using, removing the LLM-compliance fragility and silent-drift risk flagged in [#6](https://github.com/SnowboardTechie/athena-notes/issues/6).
- `workday-planning` skill — Phase 5 forge invocation now passes `Output path: return-only` instead of the prior prompt-level "don't write" override. Dependencies note and Guardrail 6 updated to match the new contract; the interim `> Note — tracked in #6` block is removed. Resolves [#6](https://github.com/SnowboardTechie/athena-notes/issues/6).

### Fixed
- `ship` skill — removed dangling reference to a `worktrunk` skill that does not exist; surfaced by the new frontmatter-lint workflow on first run.

## [0.3.0] — 2026-04-22

### Added
- `issue-create` skill (`plugins/athena-notes/skills/issue-create/`) and `/issue-create` slash command. Q&A-driven drafting of GitHub/Forgejo issues: detects forge and repo, scans `.github/ISSUE_TEMPLATE/` for field-based templates or falls back to a six-section default structure, asks clarifying questions, writes a draft to `.notes/.agents/drafts/` for review, runs a best-effort dedup check, posts via `gh issue create`, sets the template's `type:` via the GraphQL `updateIssueIssueType` mutation (with per-repo ID cache + verify-and-retry), archives the draft on success, and offers to hand off to `/issue-work`. Addresses [#10](https://github.com/SnowboardTechie/athena-notes/issues/10).
- `issue-work` skill (`plugins/athena-notes/skills/issue-work/`) migrated into the plugin, with `ticket-analyst` and `impl-reviewer` agents. Four-phase workflow (intake → plan → implement → self-review) for taking a ticket URL to review-ready implementation. `impl-reviewer` now carries its three lens prompts (correctness / security / simplicity) inline so the plugin is self-contained — no hard dependency on external `code-review` / `security-review` / `simplify` skills. Phase 4.3 ends with an explicit ship prompt that delegates to the `ship` skill on approval (instead of rolling its own `git push` + `gh pr create`), so PRs get template-based descriptions, Forgejo API support, and label application for free.
- `.github/PULL_REQUEST_TEMPLATE.md` — prompts PR authors to pick a changelog mode (non-release / release / exempt) and surfaces the post-merge `gh release create` step so release PRs don't ship without a tag.

### Fixed
- `ship` Step 6 — instruction to "remove lines starting with `>`" missed this repo's own PR template, which uses `<!-- … -->` HTML comments. The rule now covers both comment styles.

### Changed
- `ship` skill — Step 6 (Fill Description) now has an explicit source-of-truth priority: if the invoker passes a review/summary artifact, read it first and use its findings as the authoritative source for narrative sections. Previously, `/ship` filled sections from commit history only, which meant `issue-work`'s Phase 4 review summary never informed the PR body.
- `agent-workspace` skill — adds **Archive Pattern** section codifying the `_archive/{domain}/{YYYY-MM-DD}-{slug}.md` path convention, canonical-artifact footer, and archive-vs-delete rules. Lifecycle Rules table extended with a "Draft posted/promoted" row. Consumed by `issue-create` for post-success draft moves; available for any skill that produces a canonical artifact from a working file.
- `archivist` agent gains a first-class `scope:` keyword (`published` | `working` | `both`, default `both`) that callers place on the first line of the prompt to narrow the search. `session-review` Step 2 now leads with `scope: published` instead of the prior prose-level "Scope: published notes, not .agents/ working files." override — removes the silent-drift risk flagged in [#3](https://github.com/SnowboardTechie/athena-notes/issues/3). `workday-planning`'s two `.notes/.agents/forge/`-targeted archivist calls (Phase 4 week-prep, Phase 6 wins pull) also migrated to `scope: working` — path-specific globs previously carried the narrowing intent implicitly; now the contract is explicit. Backward-compatible: callers that omit the keyword get the existing both-locations behavior.
- `plugins/athena-notes/AGENTS.md` gains three new conventions under existing sections:
  - **Vault reads must filter dot-prefixed dirs** (under *Working State vs Permanent Notes*) — skills reading markdown via file globs must drop any path with a `.`-prefixed segment to match Obsidian's UI semantics and prevent feedback loops from agent working files like `.agents/forge/today.md`.
  - **`main` is protected** (under *Git & Commits*) — direct pushes to `main` are rejected; all changes land via PR, even when the user says "commit to main".
  - **Changelog-first, release-on-bump** (replaces the interim "Versioning CI gates PRs" rule) — every PR touching a versionable path updates `CHANGELOG.md`; non-release PRs accumulate under `[Unreleased]`, release PRs promote `[Unreleased]` under a new `## [x.y.z]` heading and bump `plugin.json`. Aligns with [Keep a Changelog](https://keepachangelog.com) instead of releasing on every commit.
- `plugins/athena-notes/AGENTS.md` — adds **GitHub Actions hardening baseline** convention under *Git & Commits*: every workflow ships with `permissions: contents: read` (or narrower) and a `concurrency` block keyed on `${{ github.ref }}` with `cancel-in-progress: true`. Codifies the pattern adopted in `docs-lint.yml` (#24); flags `version-check.yml` as a backfill candidate.
- `.github/workflows/version-check.yml` — split into two modes: non-release PRs just require `CHANGELOG.md` in the diff; release PRs (version bumped) keep the full footer/section checks. Repo URL now read from `${{ github.repository }}` so forks don't silently break CI.
- `plugins/athena-notes/AGENTS.md` — adds **When to add a new spoke (subagent) vs. keep work in a skill** subsection under *Architecture*. Four criteria (context isolation, parallelism, reusability, specialized persona); interactive multi-turn flows explicitly called out as the wrong shape for spokes; MCP and skill contrasted as the alternatives for tool surfaces and user-facing orchestration respectively. Codifies the rubric applied when scoping [#28](https://github.com/SnowboardTechie/athena-notes/issues/28) and reviewing [#23](https://github.com/SnowboardTechie/athena-notes/issues/23).
- `plugins/athena-notes/AGENTS.md` — adds **Fixed is for previously-shipped behavior only** clause inside the *Changelog-first, release-on-bump* convention. Mid-PR iteration (fixes to code added on the same branch) folds into the **Added**/**Changed** bullet for the new feature; **Fixed** is reserved for changes to behavior users could have seen in a prior release. Readers of a release changelog never experienced the pre-fix state, so a separate Fixed bullet is noise; squash-merge preserves the iteration trail in `git log`.
- `plugins/athena-notes/AGENTS.md` — adds **Parallel agents write to distinct output paths** subsection under *Architecture*. Codifies the file-per-agent (e.g., `explore-{area-slug}.md`) and return-by-message shapes as the two safe patterns; calls out shared-file-with-heading append as the anti-pattern. Discovered during [#31](https://github.com/SnowboardTechie/athena-notes/pull/31) and resolves [#36](https://github.com/SnowboardTechie/athena-notes/issues/36).
- `plugins/athena-notes/AGENTS.md` — new **Skill Authoring** top-level section with two subsections. *Positive prompts for approval gates*: skills at action gates (open PR, post note, send message) script the question positively with accepted replies, rather than stating a prohibition and leaving the orchestrator to invent the prompt shape — resolves [#33](https://github.com/SnowboardTechie/athena-notes/issues/33). *Per-user config vs per-project state vs plugin-local*: three-surface storage model (`~/.claude/athena/` for user config, `.notes/.agents/{skill}/` for project state, plugin body for static content) with a decision rule and worked examples — resolves [#32](https://github.com/SnowboardTechie/athena-notes/issues/32). Both were discovered in the [#31](https://github.com/SnowboardTechie/athena-notes/pull/31) review pass.

## [0.2.0] — 2026-04-21

### Added
- `workday-planning` skill (`plugins/athena-notes/skills/workday-planning/`) and `/plan-workday` slash command. Pulls live context from user-configured sources (Google Docs, GitHub issues/PRs, GitHub Projects V2 boards, Obsidian notes, URLs), synthesizes it, gets goals from `forge`, and writes the day's plan to the personal vault. Day-of-week adaptive (Mon = week-prep, Tue–Thu = daily, Fri = week-wrap); `--mode` override available.
- User-owned config at `~/.claude/athena/planning-sources.md` (YAML frontmatter), bootstrapped by the skill on first run — matches the `identity.md` + `/athena-setup` pattern.

### Changed
- `session-review` skill now applies approved AGENTS.md additions via direct `Edit` after explicit user approval, instead of presenting a copy-paste block. The user can still opt into copy-paste mode by asking for it. Guardrails updated to gate on approval rather than on the write mechanism.

## [0.1.0] — 2026-04-21

First public release. Complete port from the OpenCode/OhMyOpenAgent implementation, plus a polish pass to get the repo ready for external contributors.

### Added
- Hub-spoke agent roster: `athena` (hub), `scribe`, `archivist`, `sage`, `pyre`, `prism`, `forge`, `kindle`, `scout`.
- `/athena-setup` onboarding command with pre-fill from existing Claude Code memory.
- Core skills: `obsidian`, `athena-notes`, `agent-workspace`.
- Utility skills: `session-review`, `find-skills`, `dependency-review`, `dependency-triage`, `update-pr-description`, `ship`.
- Example agents and skills under `plugins/athena-notes/examples/`.
- Framework spec at `plugins/athena-notes/AGENTS.md` (cross-tool portable).
- Claude Code `plugin.json` manifest, marketplace metadata, AGPL-3.0-or-later license.
- `CONTRIBUTING.md` — submission workflow, four-point filter, frontmatter conventions.
- `CHANGELOG.md` — this file.
- `plugins/athena-notes/examples/README.md` — per-example adaptation guide.
- README Troubleshooting section covering identity, vault routing, sage MCP fallbacks, permission prompts, and worktree `.notes/` resolution. The "permissions keep prompting" bullet points users at `/athena-setup` Phase 5, which already writes a resolved, absolute allowlist to `~/.claude/settings.json` — so no project-local template is needed.
- README link to `AGENTS.md` as the framework spec for contributors.

### Changed
- Example agents (`calliope`, `aria`, `gamedev`) migrated from OpenCode frontmatter to Claude Code format (`name`, `description`, `tools` as comma string, `model`). Each description now flags its personal/domain-specific scope.
- `weekly-planning` skill moved from `plugins/athena-notes/skills/` to `plugins/athena-notes/examples/skills/` — it's built around Bryan's personal VOMIT framework and a fixed `second-brain` vault path, which makes it a reference example, not a general utility. SKILL.md now has a disclaimer at the top.
- `sprint-deliverable-update` example skill SKILL.md now flags its HHS/Simpler Grants conventions explicitly at the top.
- `session-review` skill tightened with a Signal Test — every candidate now has to pass four gates (novel, project-specific, future-actionable, readable in six months) before being drafted. Removed the "3-5 insights" quota that pushed toward padding; zero survivors is now explicitly the normal outcome. Added guardrails against prose-heavy narratives and quota-hitting.

### Fixed
- `session-review` skill now checks `.notes/` for existing notes on each candidate topic (via `@archivist`) before drafting, and supports proposing **updates** to existing notes instead of silently creating duplicates. Previously the dedup rule only covered `AGENTS.md`, so repeated session reviews produced parallel notes on the same subject. Output templates gain an "update" variant; Step 6 gains a scribe call shape for edits.

### Removed
- `PORTING.md` — internal tracker from the OpenCode → Claude Code port. The port is done; the file was stale (GitHub repo already exists, "remaining" items all landed). Historical context preserved in git history.

[Unreleased]: https://github.com/SnowboardTechie/athena-notes/compare/v0.4.3...HEAD
[0.4.3]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.4.3
[0.4.2]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.4.2
[0.4.1]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.4.1
[0.4.0]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.4.0
[0.3.0]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.3.0
[0.2.0]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.2.0
[0.1.0]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.1.0
