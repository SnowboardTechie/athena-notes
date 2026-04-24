# Contributing to Athena Notes

Issues and PRs welcome. This plugin is maintained in the open because the hub-spoke thinking/capture pattern works better the more eyes it gets.

## Before you start

Read [`plugins/athena-notes/AGENTS.md`](plugins/athena-notes/AGENTS.md). It's the framework spec — identity, vault routing, worktree resolution, the "users talk only to Athena" convention, cross-tool portability rules. Every agent and skill in this plugin obeys it. Yours should too.

If your contribution is host-agnostic prose (skill bodies, agent personas, templates, vault spec), also read [`core/AGENTS.md`](core/AGENTS.md). It defines the boundary between content that belongs under `core/` and content that belongs in a host-specific layer like `plugins/athena-notes/`.

## The five-point filter (for agents & skills)

Before opening a PR that adds an agent or skill to the main tree, check:

1. **Does it serve the thinking + note-capture core?** Not every useful utility belongs here. A Godot project assistant is useful, but it isn't about thinking — it's an example, not a utility.
2. **Is it Obsidian-aware?** Wikilinks, frontmatter, and the existing vault structure should feel native. If your skill writes raw JSON to a flat file, rethink it.
3. **Is it free of personal hardcoding?** No specific names, companies, projects, vault paths, or domain-specific jargon (VA.gov, HHS, "my SnowboardTechie brand"). Use placeholders (`{{USER_NAME}}`, `{{NOTES_ROOT}}`, `{{PERSONAL_VAULT}}`) read from `~/.claude/athena/identity.md`.
4. **Would a teammate you've never met find it useful?** If the honest answer is "only people who work exactly like me," it's an example — open a PR to `plugins/athena-notes/examples/` instead.
5. **Is it host-agnostic, or genuinely Claude-Code-specific?** Prose-only content (skill bodies, agent personas, templates) is host-agnostic and belongs eventually under [`core/`](core/AGENTS.md). Anything that calls runtime tools (`AskUserQuestion`, `Bash`), reads host config paths (`~/.claude/`), or depends on Claude-Code-specific frontmatter is host-specific and stays in `plugins/athena-notes/`. While migration is in progress, host-agnostic content can land in `plugins/athena-notes/` alongside its glue — flag the choice in your PR description so reviewers can route it later.

Hit all five → main tree. Miss one or more → `examples/`, still welcome, labeled as reference.

## Conventions you should know

### Tool-native, not Bash-native

Agents use `Glob`, `Grep`, `Read`, `Write`, `Edit`, `Task` directly. Avoid wrapping file-reading or searching in `Bash` — the native tools are faster, safer, and render better in Claude Code. Reserve `Bash` for shell-only operations (`git`, `gh`, `cd && foo`, one-shot system commands).

### Hub-spoke, not star

Users should only talk to Athena. Specialist agents (scribe, archivist, forge, etc.) include a line in their description like `"not user-facing; Athena invokes via Task"` and a matching note near the top of the body. If your new agent is meant to be user-facing, talk through whether it should be a skill invoked by Athena instead.

### Identity is authoritative

Every agent that needs `{{USER_NAME}}`, `{{TIMEZONE}}`, `{{NOTES_ROOT}}`, `{{WORKING_HOURS}}`, or `{{COGNITIVE_PEAK}}` reads `~/.claude/athena/identity.md` on startup and substitutes at runtime. Don't hardcode. Degrade gracefully if the file is missing.

### Cross-tool portable

Agent and skill bodies should read cleanly as Markdown instructions even to a human (or to Cursor, Aider, Codex). Frontmatter is Claude-Code-specific, but the prose that follows shouldn't assume a specific runtime.

### Docs conventions

Markdown links to files in this repo point at the actual `.md` file, not the directory. For skills, that's `skills/{name}/SKILL.md`; for agents, `agents/{name}.md`. Trailing-slash directory links (e.g., `skills/foo/`) render on GitHub but break in Obsidian preview, some IDEs, and some CI doc tooling. External URLs (`https://…/`) are exempt and keep their native shape.

A small CI check ([`.github/workflows/docs-lint.yml`](.github/workflows/docs-lint.yml)) enforces the rule.

### No AI attribution in commits

This project never adds `Co-authored-by: Claude` or similar trailers. You're the author.

Heads-up for Claude Code users: some default workflows inject a `Co-Authored-By: Claude` trailer automatically. If you see one on a commit you're about to push, strip it first (e.g., `git commit --amend` and delete the trailer line, or configure your setup to skip it). PRs with AI attribution trailers will be asked to rewrite before merge.

## Frontmatter shape

### Agent

```yaml
---
name: lowercase-single-word
description: One-line description with trigger hints for auto-invocation.
tools: Bash, Read, Write, Edit, Glob, Grep, Task
model: opus | sonnet | haiku | inherit
---
```

Choose `model` by workload: opus for hub/creative reframing, sonnet for most work, haiku for fast read-only retrieval.

### Skill

```yaml
---
name: skill-name
description: One-line trigger description — what the skill does and when to use it.
---
```

Skills are prose instructions keyed by name. Keep the description specific enough that Claude picks the right one without prompting.

## Workflow

1. Fork → branch → commit.
2. Run a smoke test: install your fork locally (`/plugin install ~/code/your-fork`) and invoke the new agent/skill end-to-end. Confirm scribe captures whatever it was supposed to capture.
3. Open a PR with:
   - What the agent/skill does and when it triggers.
   - Which of the four filter points it satisfies (or why it's an example).
   - A one-line transcript example if it's user-observable.
4. One reviewer will walk the code with the filter and the framework spec.

## Reporting issues

Open a [GitHub issue](https://github.com/SnowboardTechie/athena-notes/issues). Helpful content:

- What you expected.
- What happened instead.
- Your `~/.claude/athena/identity.md` (with sensitive bits redacted) — vault paths and working hours matter for reproducing behavior.
- The relevant agent/skill name and a short excerpt of the conversation.
