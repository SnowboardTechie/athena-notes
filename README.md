# cairn-notes

**A capture-first note system for Claude Code, native to Obsidian.**

cairn-notes turns conversations into durable trail markers — *cairns* — that pile up in your Obsidian vault. You capture insights, decisions, explorations, and meeting notes with one-line slash commands; the plugin handles vault routing, note-type templates, wikilinks, and worktree-aware paths so the friction stays near zero.

- **`/capture`** — capture an idea, decision, exploration, session summary, thread, or task. Auto-detects type, drops it in the right vault, links related prior notes.
- **`/recall`** — search past thinking across project vaults and your personal vault. Type-, date-, or attendee-filtered.
- **`/plan-workday`** + **`/plan-week`** — pull live context (PRs, issues, planning sources), get 3–5 goals with first steps, write the daily/weekly note.
- **`/meeting-sync`** — paste meeting notes; get a MEETING anchor plus linked DECISION / TASK / IDEA spin-offs.
- **`/session-review`** — review a session for vault-worthy insights, harness-memory preferences, and plugin issues to file.

Everything writes Obsidian-native markdown — wikilinks, frontmatter, your existing vault structure.

> **Extending or contributing?** Read [`plugins/cairn-notes/AGENTS.md`](plugins/cairn-notes/AGENTS.md) — it's the framework spec (identity, vault routing, worktree resolution, skill-and-spoke conventions, cross-tool portability) and the single source of truth for writing or porting skills and spokes.

---

## Requirements

- [Claude Code](https://claude.com/claude-code)
- An Obsidian vault (or willingness to let the plugin create `~/notes/second-brain/` for you on first use)
- Optional, improves the `sage` helper spoke: [Exa MCP](https://exa.ai), [Context7 MCP](https://context7.com)

---

## Install

```bash
# From Claude Code
/plugin install github:SnowboardTechie/cairn-notes
```

Then run setup:

```
/cairn-setup
```

`/cairn-setup` walks you through identity (~2 minutes) — it scans your existing Claude Code memory for clues (name, timezone, vault path), asks 5–7 quick questions to fill in what's missing, and writes `~/.claude/cairn/identity.md`. Re-runnable any time.

---

## First capture

```
/capture decision: switching to httpOnly cookies for refresh tokens
```

cairn-notes detects this is a DECISION (high confidence — the prefix is explicit), routes it to the right vault (`.notes/` if you're in a project repo, otherwise your personal vault), pre-links any related prior notes via the `archivist` spoke, and writes the file via the `scribe` spoke. You get back a wikilink and the path.

For freeform input, just pass the text:

```
/capture I just realized JWT rotation needs absolute expiry not just sliding
```

`/capture` auto-detects type. If confidence is medium or low, it confirms with you before writing. If your text looks like meeting notes, it hands off to `/meeting-sync` instead.

---

## Recall

```
/recall what did we decide about default models
/recall scope:both type:decision auth
/recall since:2026-04-01 attendees:bryan
```

A single match returns the full note body inline; multiple matches group results by vault. Results are published-only — agent working files in `.notes/.agents/` are excluded.

---

## Conventions

### Note locations

cairn-notes is opinionated about where notes live:

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

Skills and spokes will never add `Co-authored-by: Claude` or similar to your commit messages. You're the author.

---

## Skills and helper spokes

cairn-notes is **slash commands on top, helper spokes underneath**. You invoke skills; skills delegate to spokes via Task when context-isolation, parallelism, or specialized persona warrants it.

### User-facing slash commands

| Command | What it does |
|---|---|
| `/capture` | Capture a note with auto-detected or explicit type |
| `/recall` | Search past notes across project and personal vaults |
| `/plan-workday` | Daily plan with live PR/issue/source context |
| `/plan-week` | Weekly plan with Monday-leaning depth flow |
| `/meeting-sync` | Paste meeting notes → MEETING anchor + spin-offs |
| `/session-review` | Review a session for vault notes, prefs, plugin issues |
| `/cairn-setup` | First-run identity setup; re-runnable any time |
| `/issue-create`, `/issue-work`, `/pr-self-review`, `/ship`, `/dependency-review`, `/dependency-triage`, `/update-pr-description` | Forge/ticket workflows |

### Helper spokes (not user-facing)

| Spoke | Model | Role |
|---|---|---|
| scribe | sonnet | The only writer in the system |
| archivist | haiku | Past-note retrieval |
| sage | sonnet | External research (Exa / Context7 / grep.app / WebSearch) |
| pyre | haiku | Note deletion with tiered confirmation |
| forge | sonnet | Daily planning (goals, first steps) |
| kindle | sonnet | Flow-barrier coaching |
| scout | sonnet | Developer-forge activity for planning |
| impl-reviewer | sonnet | Single-lens implementation review |
| ticket-analyst | haiku | Issue/PR intake for `/issue-work` |

Spokes don't redirect users to a hub anymore — each spoke's description names the skills that call it, and a direct `@archivist`-style invocation works for power users.

---

## Skills always loaded

- `obsidian` — wikilinks, frontmatter, cross-reference patterns
- `cairn-notes` — note types, templates, capture patterns
- `agent-workspace` — working state conventions, worktree resolution, `.notes/` auto-setup

---

## Extending

The `plugins/cairn-notes/examples/` directory contains personal agents and skills the plugin author built for their own workflow:

- `calliope` — content writing agent (blog posts, newsletters)
- `aria` — domain-specialist agent (accessibility / VA.gov)
- `gamedev` — project-specific assistant (Godot)
- Skill examples: `catalog-review`, `manual-merge`, `sprint-deliverable-update`

Copy any of these into your own `~/.claude/agents/` or `~/.claude/skills/` and adapt. They show the patterns — make them yours. See [`examples/README.md`](plugins/cairn-notes/examples/README.md) for per-example adaptation notes.

---

## Cross-tool portability

The framework conventions live in [`plugins/cairn-notes/AGENTS.md`](plugins/cairn-notes/AGENTS.md) — readable by Cursor, Aider, Codex, and other tools. The agents and skills themselves are Claude Code-specific, but the conventions translate.

[`core/AGENTS.md`](core/AGENTS.md) is the boundary spec for host-agnostic content (skill prose, agent personas, templates) versus host-specific glue (runtime tool calls, agent frontmatter, plugin manifest). Migration issues [#15](https://github.com/SnowboardTechie/cairn-notes/issues/15)–[#17](https://github.com/SnowboardTechie/cairn-notes/issues/17) will move host-agnostic content under `core/` so that other-host adapters (e.g., the planned [opencode adapter](https://github.com/SnowboardTechie/cairn-notes/issues/21)) can consume it directly.

---

## Troubleshooting

**"`/capture` says it can't find my identity"**
Identity lives at `~/.claude/cairn/identity.md`. Run `/cairn-setup` to create or update it. Re-running is safe — it pre-fills from the existing file.

**"I want to change my vault location"**
Edit `personal_vault` (or `notes_root`) in `~/.claude/cairn/identity.md`. The next invocation picks up the change.

**"Scribe keeps writing to `~/notes/second-brain/` when I'm inside a repo"**
That means the `.notes/` symlink in your repo isn't set up. Start a fresh session inside the repo and run `/capture` once — scribe creates `.notes/` → `~/notes/{repo-name}/` and adds it to `.gitignore` on first capture.

**"Sage falls back to WebSearch / WebFetch even though I installed Exa"**
Sage prefers MCPs in order: Exa → Context7 → grep.app → built-in WebSearch. Check that the MCP is listed in `claude mcp list` and authenticated. If you installed Exa after sage first ran, restart the Claude Code session.

**"Permissions keep prompting when skills read my notes"**
Run `/cairn-setup`. Phase 5 offers to configure `permissions.defaultMode: "auto"` in `~/.claude/settings.json` with a resolved, absolute allowlist covering your notes, identity file, and the Bash shapes the spokes use. You'll see the exact config before it's written. If you prefer manual control, skip Phase 5 and approve-and-remember each path on first prompt instead.

**"I'm in a git worktree and notes aren't showing up"**
`.notes/` lives in the **trunk** (main worktree) so it's shared across every branch worktree. Agent-workspace resolves the trunk root automatically via `git rev-parse`. If something still looks off, `ls -la .notes` in the trunk to confirm the symlink.

---

## License

**AGPL-3.0-or-later.** See [`LICENSE`](./LICENSE).

This is free software and will stay free. Fork it, modify it, ship it — but modifications must remain AGPL, and if you run a modified version as a network service, you must share your source.

This license was chosen to prevent enclosure: cairn-notes should never become a private profit machine that takes from the commons without giving back.

---

## Contributing

Issues and PRs welcome at [github.com/SnowboardTechie/cairn-notes](https://github.com/SnowboardTechie/cairn-notes). See [CONTRIBUTING.md](CONTRIBUTING.md) for the submission workflow and conventions.

Before contributing an agent or skill, check the five-point filter:
- Does it serve the capture / recall / planning core? (vs. being a random utility)
- Is it Obsidian-aware? (wikilinks, frontmatter, vault conventions)
- Is it free of personal hardcoding? (no specific names, companies, projects)
- Would a teammate you've never met find it useful?
- Is it host-agnostic, or genuinely Claude-Code-specific? (see [`core/AGENTS.md`](core/AGENTS.md))

If yes to all five, open a PR to the main `agents/` or `skills/` tree. If no to one or more, it probably belongs in `examples/` — still welcome, but labeled as a reference, not a utility.

---

## Acknowledgments

- The "cairn" metaphor — trail markers your agents leave behind — owes the commonplace-book tradition to the Obsidian community and the idea of marking your own trail to anyone who's ever hiked above the tree line.
- Inspired in part by Daniel Miessler's [PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) system — we went a different direction on persona and orchestration, but the personal-knowledge-system concept and the TELOS framing are kin.
