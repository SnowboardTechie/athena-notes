# core/ — host-agnostic content

This directory is the home for content that doesn't depend on any specific agent runtime. Skill prose, agent personas, vault patterns, note templates, and the framework spec itself can live here unchanged across [Claude Code](https://claude.com/claude-code), [opencode](https://opencode.ai), [Cursor](https://cursor.com), Aider, Codex, and any future host that respects the [`AGENTS.md`](https://agents.md) convention.

This file is the spec for what belongs here. If you're adding a skill, agent, or template and you're not sure where to put it — start here.

## The boundary

Two layers exist in this repo:

- **Host-agnostic** (this directory): prose instructions, conventions, and templates that read cleanly as Markdown to any reasonable LLM-driven agent runtime. No specific tool names, no host-specific config paths, no runtime-specific frontmatter.
- **Host-specific** (under `plugins/{plugin-name}/` for now; eventually also under `adapters/{host}/`): the glue that makes the host-agnostic content executable on a particular runtime. Plugin manifests, runtime tool calls (`AskUserQuestion`, `Bash`, etc.), agent frontmatter (`tools:`, `model:`), runtime config paths (`~/.claude/`, `.opencode/`, …), and slash-command surfaces.

The relationship is one-directional: host-specific layers consume host-agnostic content. Nothing in `core/` should reference anything in `plugins/` or `adapters/`. The opposite — a Claude Code plugin or an opencode adapter pulling skill prose from `core/skills/` — is the point.

## What belongs here

A piece of content is host-agnostic if all four are true:

1. **No runtime-specific tool calls.** No `AskUserQuestion`, no `Bash` blocks, no Claude-Code-shaped tool invocations. Skills express *what* to do; the host adapter binds *how*.
2. **No host-specific config paths.** No `~/.claude/`, no `.opencode/`, no plugin-manifest references. Configurable paths come from the host adapter or from a shared identity contract the adapter resolves.
3. **No frontmatter that only one runtime understands.** Claude Code's `tools: Bash, Read, Write` frontmatter is host-specific; opencode's `tools: [bash, read, write]` shape is host-specific. The agent persona — name, description, role, behaviors — is host-agnostic; the tool binding is not.
4. **Reads cleanly to a human.** A contributor who has never used the runtime should be able to read the file and understand what the agent or skill does, even if they can't run it without an adapter.

When in doubt, ask: *would this file still make sense if Claude Code didn't exist?* If yes, it's a `core/` candidate.

## What doesn't belong here

- Plugin manifests (`.claude-plugin/plugin.json`, `package.json`, opencode equivalents).
- Slash-command files (`commands/*.md`) — the syntax is host-specific.
- Setup commands that write to `~/.claude/settings.json` or any host's config home.
- Skills that depend on `AskUserQuestion` for control flow. (Interactive Q&A is a host-specific surface — adapters bind it differently. The host-agnostic version of a Q&A skill describes the *information needed* and the *decisions to make*; the adapter wires the actual prompts.)
- Agent frontmatter (`tools:`, `model:`).

These belong in the host-specific layer for whichever runtime they target.

## Where new content goes — decision rule

```
Is the content runtime-bound (tool calls, frontmatter, config paths)?
├── Yes → host-specific layer (today: plugins/athena-notes/; future: adapters/{host}/)
└── No → core/
```

For agents and skills specifically:

- **Agent prose** (description, role, behaviors, conventions) → `core/`. Frontmatter (tools, model) → host-specific.
- **Skill body** (what the skill does, when to use it, the workflow) → `core/`. Anything that depends on a runtime tool to execute → host-specific.
- **Templates / vault spec / note types** → `core/`. These are pure data shapes.
- **Setup or onboarding flows** that touch a host's config home → host-specific.

If a skill is *mostly* host-agnostic but has one or two host-specific calls, the question is whether to extract the host-agnostic prose into `core/` and have the host-specific layer re-export it. That's a per-skill judgment to make at migration time, not now.

## Current state (April 2026)

This PR establishes `core/` as a documented destination. Existing host-agnostic content has not yet been migrated — it still lives under `plugins/athena-notes/` alongside its host-specific glue. That's deliberate scope-narrowing; migration is what subsequent issues in the [Make Athena Notes portable to opencode](https://github.com/SnowboardTechie/athena-notes/issues?q=is%3Aissue+epic+portable) epic are for. Until those land:

- `plugins/athena-notes/AGENTS.md` remains the active framework spec for the Claude Code plugin.
- `plugins/athena-notes/skills/` and `plugins/athena-notes/agents/` remain the active skill and agent trees.
- New skills and agents can land in either location depending on which scope they fit; flag the choice in the PR description so it's visible.

## Future shape

The intended layout, once migration completes:

```
core/
├── AGENTS.md           # this file — boundary spec + framework conventions
├── agents/             # agent persona/prose (frontmatter lives in adapters/)
├── skills/             # skill bodies (host-specific calls factored out)
├── templates/          # note templates, vault spec
└── examples/           # reference content not in the main tree

adapters/
├── claude-code/        # Claude Code adapter — frontmatter, plugin manifest, host-specific commands
└── opencode/           # opencode adapter — frontmatter, plugin shape, lifecycle hooks (see #21)
```

Today's `plugins/athena-notes/` is in effect the Claude Code adapter. Whether it's renamed to `adapters/claude-code/`, kept at `plugins/athena-notes/` for marketplace compatibility, or split between the two is a decision for the migration PRs — not this one.

## Explicit deferrals

This PR does not:

- Move `plugins/athena-notes/AGENTS.md` into `core/`. The two specs coexist with a forward-pointer until a migration PR symlinks or merges them.
- Migrate any skill, agent, or template into `core/`.
- Create `adapters/` or any subdirectory of `core/`.
- Update `.github/workflows/version-check.yml` to cover `core/**`. The first PR that adds versionable content under `core/` adds the glob.
- Update `scripts/lint-frontmatter.py`. No frontmatter-bearing files land here in this PR.

If you're picking up the next subissue in the epic, the natural starting points are: (1) decide whether `core/AGENTS.md` should absorb `plugins/athena-notes/AGENTS.md`'s framework conventions or stay separate as the boundary spec, and (2) pick a single host-agnostic skill (likely [`athena-notes`](../plugins/athena-notes/skills/athena-notes/SKILL.md) or [`obsidian`](../plugins/athena-notes/skills/obsidian/SKILL.md)) to migrate as the proof of concept.

## Cross-references

- [`plugins/athena-notes/AGENTS.md`](../plugins/athena-notes/AGENTS.md) — current framework spec for the Claude Code plugin (identity, vault routing, hub-spoke architecture, skill authoring, git conventions). This file (`core/AGENTS.md`) defines the boundary; that file defines the conventions agents follow inside the boundary.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — submission workflow including the host-agnostic check in the contribution filter.
- [#14](https://github.com/SnowboardTechie/athena-notes/issues/14) — issue that established this file.
- [#21](https://github.com/SnowboardTechie/athena-notes/issues/21) — planned opencode adapter; first real test of the portability thesis.
