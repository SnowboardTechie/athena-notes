# Athena Notes

**An Obsidian-native thinking and note-capture system for Claude Code.**

Athena Notes is a hub-spoke of specialized AI agents that help you think, research, and capture knowledge — with your notes landing directly in Obsidian vaults in Obsidian-native formats.

- **Athena** is your thinking partner. Talk to her for anything — thinking, planning, capturing, recalling, research, focus, flow.
- Behind her, a roster of specialist subagents: **Scribe** writes, **Archivist** searches, **Sage** researches, **Pyre** deletes, **Prism** refracts ideas, **Forge** structures planning, **Kindle** coaches flow.
- You only talk to Athena. The subagents are her tools, not yours.
- Everything writes to Obsidian using wikilinks, frontmatter, and your existing vault structure.

> **Extending or contributing?** Read [`plugins/athena-notes/AGENTS.md`](plugins/athena-notes/AGENTS.md) — it's the framework spec (identity, vault routing, worktree resolution, agent invocation conventions, cross-tool portability) and the single source of truth for writing or porting agents and skills.

---

## Requirements

- [Claude Code](https://claude.com/claude-code)
- An Obsidian vault (or willingness to let the plugin create `~/notes/second-brain/` for you on first use)
- Optional but recommended for `sage` agent: [Exa MCP](https://exa.ai), [Context7 MCP](https://context7.com)

---

## Install

```bash
# From Claude Code
/plugin install github:SnowboardTechie/athena-notes
```

After installing, **start a new session and talk to athena**. She will detect that Athena Notes isn't set up yet and walk you through identity setup (~2 minutes).

Or run setup explicitly:

```
/athena-setup
```

---

## First Use

On first invocation, athena will:

1. Scan your existing Claude Code setup for identity clues (name, timezone, etc.)
2. Ask 5-7 quick questions to fill in what's missing
3. Write `~/.claude/athena/identity.md`
4. Continue with your original request

After that, agents know who you are. You can update identity any time by re-running `/athena-setup`.

---

## Conventions

### Note locations

Athena Notes is opinionated about where notes live:

| Scenario | Notes go to |
|---|---|
| Inside a git repo | `.notes/` → `~/notes/{repo-name}/` (auto-created) |
| Inside `~/notes/second-brain/` | `./` (current dir is the vault) |
| Anywhere else | `~/notes/second-brain/` (personal vault) |

The `.notes/` symlink is created automatically the first time you work in a new repo. It's added to `.gitignore` so your notes don't pollute commits.

### Vaults

- `~/notes/second-brain/` is the default personal vault (auto-created on first use)
- Project vaults at `~/notes/{project-name}/` are auto-created per repo
- You can add other named vaults at `~/notes/*/` — the plugin discovers them at runtime

### No AI attribution in commits

Agents will never add `Co-authored-by: Claude` or similar to your commit messages. You're the author.

---

## Usage

Talk to Athena for everything. She decides which subagent to engage behind the scenes.

**Thinking through a problem:**

```
athena, I'm torn between JWT and session auth for this new API. help me think through it.
```

She pulls past notes via archivist, maybe grabs external research via sage, captures insights via scribe.

**Planning your day:**

```
athena, help me plan tomorrow
```

Athena delegates to forge for goal-focused planning — 3–5 daily goals with first steps. No clock times or focus blocks unless you ask for them.

**Getting unstuck:**

```
athena, I can't get started on the auth task
```

Athena delegates to kindle for flow-barrier coaching (anxiety / boredom / distraction).

**Capturing something specific:**

```
athena, capture this decision: we're going with httpOnly cookies for refresh tokens
```

Athena hands the full context to scribe.

**Finding past thinking:**

```
athena, what have we explored about auth before?
```

Athena delegates to archivist.

The pattern: you talk to Athena; Athena handles routing.

---

## The agents

**User-facing:**

| Agent | Model | Role |
|---|---|---|
| athena | opus | The one agent you talk to. Hub + thinking partner. |

**Subagents (Athena invokes these for you):**

| Agent | Model | Role |
|---|---|---|
| scribe | sonnet | Writes notes, drafts, task context |
| archivist | haiku | Retrieves past thinking |
| sage | sonnet | External research (Exa / Context7 / grep.app / WebSearch) |
| pyre | haiku | Deletes notes with tiered confirmation |
| prism | opus | Creative refractor — paradoxes, unnamed concepts |
| forge | sonnet | Daily planning (goals, first steps) |
| kindle | sonnet | Flow-barrier coaching |

---

## Skills

Core skills (always loaded):

- `obsidian` — wikilinks, frontmatter, cross-reference patterns
- `athena-notes` — note types, templates, capture patterns
- `agent-workspace` — working state conventions, worktree resolution, `.notes/` auto-setup

Utility skills (available when relevant):

- `session-review`, `find-skills`, `dependency-review`, `dependency-triage`, `update-pr-description`, `ship`

---

## Extending

The `plugins/athena-notes/examples/` directory contains personal agents and skills the plugin author built for their own workflow:

- `calliope` — content writing agent (blog posts, newsletters)
- `aria` — domain-specialist agent (accessibility / VA.gov)
- `gamedev` — project-specific assistant (Godot)
- Skill examples: `catalog-review`, `manual-merge`, `sprint-deliverable-update`

Copy any of these into your own `~/.claude/agents/` or `~/.claude/skills/` and adapt. They show the patterns — make them yours. See [`examples/README.md`](plugins/athena-notes/examples/README.md) for per-example adaptation notes.

---

## Cross-tool portability

The framework conventions live in `AGENTS.md` — readable by Cursor, Aider, Codex, and other tools. The agents and skills themselves are Claude Code-specific, but the conventions translate.

[`core/AGENTS.md`](core/AGENTS.md) is the boundary spec for host-agnostic content (skill prose, agent personas, templates) versus host-specific glue (runtime tool calls, agent frontmatter, plugin manifest). Subsequent migration issues will move host-agnostic content under `core/` so that other-host adapters (e.g., the planned [opencode adapter](https://github.com/SnowboardTechie/athena-notes/issues/21)) can consume it directly.

---

## Troubleshooting

**"athena doesn't know who I am"**
Identity lives at `~/.claude/athena/identity.md`. Run `/athena-setup` to create or update it. Re-running is safe — it pre-fills from the existing file.

**"I want to change my vault location"**
Edit `personal_vault` (or `notes_root`) in `~/.claude/athena/identity.md`. The next agent invocation picks up the change.

**"Scribe keeps writing to `~/notes/second-brain/` when I'm inside a repo"**
That means the `.notes/` symlink in your repo isn't set up. Start a fresh session inside the repo and ask athena to "set up the workspace here" — it will create `.notes/` → `~/notes/{repo-name}/` and add it to `.gitignore`.

**"Sage falls back to WebSearch / WebFetch even though I installed Exa"**
Sage prefers MCPs in order: Exa → Context7 → grep.app → built-in WebSearch. Check that the MCP is listed in `claude mcp list` and authenticated. If you installed Exa after sage first ran, restart the Claude Code session.

**"Permissions keep prompting when athena reads my notes"**
Run `/athena-setup`. Phase 5 offers to configure `permissions.defaultMode: "auto"` in `~/.claude/settings.json` with a resolved, absolute allowlist covering your notes, identity file, and the Bash shapes the spokes use. You'll see the exact config before it's written. If you prefer manual control, skip Phase 5 and approve-and-remember each path on first prompt instead.

**"I'm in a git worktree and notes aren't showing up"**
`.notes/` lives in the **trunk** (main worktree) so it's shared across every branch worktree. Agent-workspace resolves the trunk root automatically via `git rev-parse`. If something still looks off, `ls -la .notes` in the trunk to confirm the symlink.

---

## License

**AGPL-3.0-or-later.** See [`LICENSE`](./LICENSE).

This is free software and will stay free. Fork it, modify it, ship it — but modifications must remain AGPL, and if you run a modified version as a network service, you must share your source.

This license was chosen to prevent enclosure: Athena Notes should never become a private profit machine that takes from the commons without giving back.

---

## Contributing

Issues and PRs welcome at [github.com/SnowboardTechie/athena-notes](https://github.com/SnowboardTechie/athena-notes). See [CONTRIBUTING.md](CONTRIBUTING.md) for the submission workflow and conventions.

Before contributing an agent or skill, check the five-point filter:
- Does it serve the thinking + note-capture core? (vs. being a random utility)
- Is it Obsidian-aware? (wikilinks, frontmatter, vault conventions)
- Is it free of personal hardcoding? (no specific names, companies, projects)
- Would a teammate I've never met find it useful?
- Is it host-agnostic, or genuinely Claude-Code-specific? (see [`core/AGENTS.md`](core/AGENTS.md))

If yes to all five, open a PR to the main `agents/` or `skills/` tree. If no to one or more, it probably belongs in `examples/` — still welcome, but labeled as a reference, not a utility.

---

## Acknowledgments

- Inspired by Daniel Miessler's [PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) system (we went a different direction but the hub-spoke idea and TELOS concept are kin)
- Built on the shoulders of the Obsidian community's commonplace-book tradition
