# Changelog

All notable changes to Athena Notes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

_No unreleased changes._

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

[Unreleased]: https://github.com/SnowboardTechie/athena-notes/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.2.0
[0.1.0]: https://github.com/SnowboardTechie/athena-notes/releases/tag/v0.1.0
