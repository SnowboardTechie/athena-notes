# Athena Notes

**An Obsidian-native thinking and note-capture system for Claude Code.**

Athena Notes is a hub-spoke of specialized AI agents that help you think, research, and capture knowledge — with your notes landing directly in Obsidian vaults in Obsidian-native formats.

- **Muse** is your thinking partner. Ask her anything.
- She delegates to **Scribe** (writes), **Archivist** (searches past notes), **Sage** (external research), **Pyre** (deletes), and **Prism** (refracts ideas into breakthroughs).
- **Forge** and **Kindle** help you focus and get unstuck when flow breaks.
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
/plugin install github:bryan-thompsoncodes/athena-notes
```

After installing, **start a new session and talk to muse**. She will detect that Athena Notes isn't set up yet and walk you through identity setup (~2 minutes).

Or run setup explicitly:

```
/athena-setup
```

---

## First Use

On first invocation, muse will:

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

### Thinking with muse

Just talk to her:

```
muse, I'm torn between JWT and session auth for this new API. help me think through it.
```

She'll pull past notes via archivist, maybe grab external research via sage, and capture insights as they emerge via scribe. You don't call any of those directly — muse orchestrates.

### Deep work with forge

```
forge, plan my deep work for today
```

Forge asks about priorities, sequences tasks by cognitive load (using your working hours and peak window from identity), and tracks blocks. Handoff to kindle if you get stuck.

### Getting unstuck with kindle

```
kindle, I can't start on the auth task
```

Kindle diagnoses the flow barrier (anxiety / boredom / distraction) and gives tailored tactics. Handoff back to forge when you're ready to go.

---

## The agents

| Agent | Model | Role |
|---|---|---|
| muse | opus | Thinking hub, orchestrates subagents |
| prism | opus | Creative refractor, reveals paradoxes and breakthroughs |
| scribe | sonnet | Note persistence (invoked by other agents only) |
| sage | sonnet | External research (Exa/Context7/WebSearch) |
| forge | sonnet | Deep work planning and block tracking |
| kindle | sonnet | Flow state coaching |
| archivist | haiku | Fast note retrieval |
| pyre | haiku | Note deletion with confirmation |

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

Issues and PRs welcome at [github.com/bryan-thompsoncodes/athena-notes](https://github.com/bryan-thompsoncodes/athena-notes).

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
