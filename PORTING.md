# Porting Tracker

Status of the port from OpenCode/OhMyOpenAgent to Claude Code plugin. Not shipped — internal doc for plugin development.

## Done

- [x] Directory scaffold (`.claude-plugin/`, `agents/`, `commands/`, `skills/`, `examples/`)
- [x] `plugin.json` — Claude Code plugin manifest
- [x] `LICENSE` — AGPL v3 (canonical text from gnu.org)
- [x] `AGENTS.md` — framework conventions (cross-tool portable)
- [x] `CLAUDE.md` — thin importer pointing to AGENTS.md
- [x] `README.md` — install, setup, usage, license rationale
- [x] `commands/athena-setup.md` — onboarding flow with pre-fill from existing Claude Code memory
- [x] `agents/muse.md` — reference port (demonstrates all translations)
- [x] `skills/agent-workspace/` — rewritten from scratch (worktrunk refs removed, vault auto-setup docs added)
- [x] `skills/obsidian/` — copied + de-Bryan'd (vault table removed, vault discovery via identity)
- [x] `skills/athena-notes/` — copied from `~/.claude/skills/` (identical content, no changes needed)
- [x] `skills/session-review/` — copied
- [x] `skills/find-skills/` — copied (wording update pending; see below)
- [x] `skills/weekly-planning/` — copied (VOMIT system, personal-vault-scoped)
- [x] `skills/dependency-review/` — copied
- [x] `skills/dependency-triage/` — copied
- [x] `skills/update-pr-description/` — copied
- [x] `skills/ship/` — copied from OpenCode
- [x] `examples/agents/{calliope,aria,gamedev}.md` — raw OpenCode copies (still have OpenCode frontmatter, needs cleanup before shipping as examples)
- [x] `examples/skills/{catalog-review,manual-merge,sprint-deliverable-update}/` — copied

## Remaining

### Agents to port (7)

For each: translate OpenCode frontmatter → Claude Code frontmatter, rewrite `mcp_task(...)` invocations → `Task(...)`, replace "Bryan" → `{{USER_NAME}}`, drop workday/burnt-ice vault refs, set appropriate model.

| Agent | Model | Complexity | Special notes |
|---|---|---|---|
| archivist | haiku | Low | Simple search + summarize loop |
| pyre | haiku | Low | Deletion with tiered confirmation. Must preserve safety protocol. |
| scribe | sonnet | **Medium-high** | Delete "Obsidian-Specific (Workday Vault Only)" section. Simplify path resolution to 3 modes (project/direct vault/default-personal-vault). |
| sage | sonnet | Medium | Needs graceful MCP degradation: prefer Exa/Context7/grep.app if present, fall back to WebSearch + WebFetch. |
| forge | sonnet | Medium | Working hours + cognitive peak come from identity, not hardcoded. |
| kindle | sonnet | Low | No significant Bryan-isms. |
| prism | opus | Low | Creative refractor, uses extended thinking. |

### Skill cleanups (post-copy)

- [ ] `skills/find-skills/` — update wording from "OhMyOpenAgent format" to Claude Code skill/agent format
- [ ] `skills/athena-notes/` — audit for any workday/burnt-ice/VA references; generalize if found
- [ ] `skills/weekly-planning/` — check for VA.gov / Simpler Grants refs; generalize or move to examples
- [ ] `skills/session-review/` — verify "AGENTS.md and .notes/" phrasing is still accurate (it should be — we're using AGENTS.md)
- [ ] `skills/ship/` — verify no worktrunk-specific refs; it uses `wt` hooks in some paths

### Examples cleanup

- [ ] `examples/agents/calliope.md` — translate frontmatter, add README to examples/ explaining "copy and adapt"
- [ ] `examples/agents/aria.md` — translate frontmatter
- [ ] `examples/agents/gamedev.md` — translate frontmatter
- [ ] `examples/skills/*` — verify all have standard skill frontmatter
- [ ] `examples/README.md` — write "these are personal agents/skills, copy and adapt for your own projects"

### Translations reference (apply to every agent port)

**Frontmatter:**
```yaml
# OpenCode (remove)
mode: subagent
hidden: true
model: openai/gpt-5.4 | openai/gpt-5.4-mini
temperature: 0.1 - 0.7
thinking:
  type: enabled
  budgetTokens: 16000-64000
tools:
  bash: true
  read: true
  write: false
skills:
  - obsidian

# Claude Code (replace with)
name: {lowercase}
description: {one-line, with trigger hints for auto-invocation}
tools: Bash, Read, Glob, Grep, Task, ...  # comma-separated names
model: opus | sonnet | haiku | inherit
```

**Invocation syntax:**
```python
# OpenCode
mcp_task(subagent_type="archivist", load_skills=[], description="...", prompt="...", run_in_background=false)

# Claude Code
Task(subagent_type="archivist", description="...", prompt="...")
```

**Name replacement:** `Bryan` → `{{USER_NAME}}` throughout agent body. Agents read identity file on startup and substitute.

**Vault references:** Remove all refs to `workday`, `burnt-ice`. `second-brain` stays as `{{PERSONAL_VAULT}}` (defaulted during setup). Runtime vault discovery via `ls {{NOTES_ROOT}}/*/`.

### Open items

- [ ] Decide if `examples/` agents need full port to Claude Code format or ship as-is with a note "these were built for OpenCode; adapt as you see fit"
- [ ] Sprint-deliverable-update skill has HHS-specific process knowledge — ensure it's clearly flagged as example, not utility
- [ ] After all agents ported, do one final pass to verify cross-references work (muse mentions archivist/sage/etc — all names must match)
- [ ] First-session smoke test: install plugin locally, run `/athena-setup`, ask muse something, confirm scribe auto-capture works
- [ ] Create GitHub repo `bryan-thompsoncodes/athena-notes`, push, verify `gh auth` allows `/plugin install github:...` path

---

## Commands to run when ready

### Local install for testing

```bash
# From within a Claude Code session
/plugin install ~/code/athena-notes
```

### Publish when ready

```bash
cd ~/code/athena-notes
git init
git add .
git commit -m "Initial plugin scaffold"
gh repo create bryan-thompsoncodes/athena-notes --public --source=. --remote=origin --push
```

Then set up mirrors to Forgejo and Codeberg.
