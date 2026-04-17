# Athena Notes

**An Obsidian-native thinking and note-capture system for Claude Code.**

Athena Notes is a hub-spoke of specialized AI agents that help you think, research, and capture knowledge — with your notes landing directly in Obsidian vaults in Obsidian-native formats.

- **Athena** is your thinking partner. Talk to her for anything — thinking, planning, capturing, recalling, research, focus, flow.
- Behind her, a roster of specialist subagents: **Scribe** writes, **Archivist** searches, **Sage** researches, **Pyre** deletes, **Prism** refracts ideas, **Forge** structures planning, **Kindle** coaches flow.
- You only talk to Athena. The subagents are her tools, not yours.
- Everything writes to Obsidian using wikilinks, frontmatter, and your existing vault structure.

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

- `session-review`, `find-skills`, `weekly-planning`, `dependency-review`, `dependency-triage`, `update-pr-description`, `ship`

---

## Extending

The `examples/` directory contains personal agents and skills the plugin author built for their own workflow:

- `calliope` — content writing agent (blog posts, newsletters)
- `aria` — domain-specialist agent (accessibility / VA.gov)
- `gamedev` — project-specific assistant (Godot)
- Skill examples: `catalog-review`, `sprint-deliverable-update`, `manual-merge`

Copy any of these into your own `~/.claude/agents/` or `~/.claude/skills/` and adapt. They show the patterns — make them yours.

---

## Cross-tool portability

The framework conventions live in `AGENTS.md` — readable by Cursor, Aider, Codex, and other tools. The agents and skills themselves are Claude Code-specific, but the conventions translate.

---

## License

**AGPL-3.0-or-later.** See [`LICENSE`](./LICENSE).

This is free software and will stay free. Fork it, modify it, ship it — but modifications must remain AGPL, and if you run a modified version as a network service, you must share your source.

This license was chosen to prevent enclosure: Athena Notes should never become a private profit machine that takes from the commons without giving back.

---

## Contributing

Issues and PRs welcome at [github.com/SnowboardTechie/athena-notes](https://github.com/SnowboardTechie/athena-notes).

Before contributing an agent or skill:
- Does it serve the thinking + note-capture core? (vs. being a random utility)
- Is it Obsidian-aware? (wikilinks, frontmatter, vault conventions)
- Is it free of personal hardcoding? (no specific names, companies, projects)
- Would a teammate I've never met find it useful?

If yes to all four, open a PR.

---

## Acknowledgments

- Inspired by Daniel Miessler's [PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) system (we went a different direction but the hub-spoke idea and TELOS concept are kin)
- Built on the shoulders of the Obsidian community's commonplace-book tradition
