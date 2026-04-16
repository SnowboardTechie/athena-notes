# Athena Notes — Agent Framework

This file documents the conventions agents follow in the Athena Notes system. It is written in `AGENTS.md` format for cross-tool portability (Claude Code, Cursor, Aider, Codex, etc.). Claude Code can reference it via `@AGENTS.md` import in `CLAUDE.md`.

---

## Identity

User identity lives at `~/.claude/athena/identity.md` and is populated by the `/athena-setup` slash command on first use. Agents read this file at invocation to resolve `{{USER_NAME}}`, `{{TIMEZONE}}`, `{{PERSONAL_VAULT}}`, `{{WORKING_HOURS}}`, `{{COGNITIVE_PEAK}}`, and `{{PRONOUNS}}`.

**If identity is missing:**
- Athena runs `/athena-setup` inline before proceeding with the user's request
- Other agents stop and direct the user to athena or `/athena-setup`

Never hard-code user-specific values in agent bodies.

---

## Architecture

```
                              ┌─────────────┐
                              │   ATHENA    │  ← Primary thinking partner (hub)
                              └──────┬──────┘
         ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
         ▼           ▼           ▼       ▼           ▼           ▼
    ┌────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐
    │ARCHIVIST│ │   SAGE   │ │ SCRIBE │ │ PYRE │ │ PRISM  │ │ (more)  │
    │(recall) │ │(research)│ │(write) │ │(del) │ │(refract)│ │         │
    └────────┘ └──────────┘ └────────┘ └──────┘ └────────┘ └─────────┘

Independent (invoked by user directly or by athena):
    ┌────────┐ ┌────────┐
    │ FORGE  │ │ KINDLE │
    │(focus) │ │(flow)  │
    └────────┘ └────────┘
```

Scribe is **never invoked directly by users** — only by other agents. Athena gathers the context scribe needs (note type, title, related notes) before delegating.

---

## Notes System

### Vault discovery

Agents discover vaults at runtime by listing `~/notes/*/`. No vault names are hard-coded beyond the `second-brain` default for personal notes.

### Vault routing

| You're in | Insight is about | Write to |
|---|---|---|
| Project repo | This project | `.notes/` (→ `~/notes/{project}/`) |
| Project repo | Cross-project or personal | `~/notes/second-brain/` |
| `~/notes/second-brain/` | A specific project | `~/notes/{project}/` |
| `~/notes/second-brain/` | Personal / cross-cutting | `./` |
| Anywhere else | Anything | `~/notes/second-brain/` |

### Auto-setup

If an agent is invoked in a git repo without a `.notes/` symlink:
1. Create `~/notes/{project-name}/` if missing
2. Create `.notes` symlink in the trunk (never in a worktree)
3. Add `.notes` to `.gitignore` if not present
4. Proceed

If `~/notes/second-brain/` is missing on first personal-note write, auto-create it.

### Worktree resolution

Agents resolve the **trunk root** (not the current worktree) before any `.notes/` operation. `.notes` lives only in the trunk. All worktrees share it. See the `agent-workspace` skill for the resolution protocol.

---

## Working State vs Permanent Notes

- `.notes/` — permanent knowledge: ideas, explorations, decisions worth keeping
- `.notes/.agents/` — working state: task context, drafts, research cache

Working files live under `.notes/.agents/{agent-name}/` and are cleaned up when tasks complete. The `.agents/` prefix hides them from Obsidian's default view.

---

## Subagent Output Verification (mandatory)

Subagent output is **unverified**. Treat it like a junior's draft — review it, check the claims, resolve the open questions. Never relay it to the user without verification.

**Before presenting any subagent finding:**
1. If a finding references a file → read the file yourself
2. If a finding says "confirm X" or "verify Y" → that's your job, do it before reporting
3. If a finding hedges ("this may not matter", "worth checking") → investigate and give a definitive answer
4. If a finding doesn't pass a basic smell test → look at the actual code before repeating it

This applies to all delegated work: code reviews, exploration results, research summaries, implementation output. You are the senior engineer. The subagent is a tool. Verify before you report.

---

## Capture Triggers (for athena + other hub agents)

Auto-capture these moments without asking — the point of Athena Notes is low-friction capture:

| Signal | Note type | Action |
|---|---|---|
| Insight emerges | IDEA | Delegate to scribe with type=IDEA |
| Topic explored deeply | EXPLORATION | Delegate at natural pause |
| Choice made | DECISION | Record choice and rationale |
| Session ending, was valuable | SESSION | Summary before close |
| Same topic 3+ times | THREAD | Connect the dots |
| Checking ticket/PR status | TASK | Update or create task note |
| Blocker identified | TASK | Capture blocker + timeline |

Scribe writes immediately on invocation. No previews, no confirmation prompts.

---

## Git & Commits

- **No AI attribution in commits.** Never add `Co-authored-by: Claude`, `Co-Authored-By: Claude Code`, `Generated with`, or similar. The human is the sole author.
- **Atomic commits.** Small, focused commits grouped by concern, not by time.
- **Never commit unverified work.** Confirm builds pass, tests pass, no regressions before committing.
- **Feature branches only.** Never commit directly to `main`/`master` unless the user explicitly says so (rare — only in dotfile-style repos).

---

## PR Review Comments

When posting review comments to a forge (GitHub, Gitea, Forgejo), **always post as inline comments on specific files and lines** — never as a single bulk review body. Each finding is its own comment anchored to the relevant code so the author sees it in context. The review body itself should be a short summary only.

---

## Cross-Tool Compatibility

This plugin is designed primarily for Claude Code but uses `AGENTS.md` format so the conventions port to Cursor, Aider, Codex, and other tools that respect this file. The agents and skills themselves are Claude Code-specific, but forks for other platforms can use this file as the shared spec.

---

## License

AGPL-3.0-or-later. See `LICENSE`. Fork freely. Modifications must remain AGPL. If you run a modified version as a network service, you must share your source.
