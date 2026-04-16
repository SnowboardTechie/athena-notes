---
name: obsidian
description: Obsidian vault patterns - wikilinks, frontmatter, vault discovery from identity, cross-referencing, error handling. Use when reading or writing notes to any Obsidian vault.
---

# Obsidian Skill

Shared patterns for working with Obsidian vaults in the Athena Notes system.

## CRITICAL: When to Use This Skill

> **This skill is for direct vault work only.**
>
> If you're in a **project repo**, use `.notes/` instead.
> The `.notes/` symlink automatically maps to the correct project vault.

### Decision Tree

```
Working directory is a code repo (has .git, package.json, etc.)?
  YES → Use `.notes/` — DO NOT use direct vault paths
  NO  → Working dir is inside {NOTES_ROOT}/{vault}?
    YES → Use `./` (current directory)
    NO  → Default to {NOTES_ROOT}/{PERSONAL_VAULT}/ (from identity)
```

**NEVER use iCloud, Dropbox, or other sync-provider paths directly** — they contain spaces, emoji, and sync lag. Use the stable path from `~/.claude/athena/identity.md`.

---

## Vault Discovery

Vault locations come from `~/.claude/athena/identity.md`:

- `notes_root` — typically `~/notes` — root directory for all vaults
- `personal_vault` — typically `second-brain` — the default cross-project vault

Agents discover additional vaults at runtime:

```bash
NOTES_ROOT=$(grep '^notes_root:' ~/.claude/athena/identity.md | cut -d: -f2- | xargs)
NOTES_ROOT="${NOTES_ROOT/#\~/$HOME}"

# List all vaults
ls -d "${NOTES_ROOT}"/*/ 2>/dev/null
```

No vault names are hard-coded. The personal vault is the only one with a known default; all others are user-created.

---

## Wikilink Syntax

**Always use Obsidian wikilinks for cross-referencing within a vault.**

### Link Patterns

| Pattern | Syntax | Example | Use Case |
|---------|--------|---------|----------|
| Basic | `[[Note]]` | `[[GDD]]` | Link to note by name |
| Display text | `[[Note\|text]]` | `[[GDD\|design doc]]` | Custom link text |
| Header | `[[Note#Header]]` | `[[mechanics#Combat]]` | Link to section |
| Header + display | `[[Note#Header\|text]]` | `[[mechanics#Combat\|combat system]]` | Section with custom text |
| Block | `[[Note#^block-id]]` | `[[GDD#^core-loop]]` | Link to specific block |
| Embed note | `![[Note]]` | `![[template]]` | Embed full note |
| Embed section | `![[Note#Header]]` | `![[GDD#Summary]]` | Embed specific section |
| Embed image | `![[image.png]]` | `![[diagram.png]]` | Embed image |
| Embed sized | `![[image.png\|300]]` | `![[hero.png\|400]]` | Image with width |

### Best Practices

1. **Prefer wikilinks over markdown links** — `[[Note]]` not `[Note](Note.md)`
2. **Use display text for clarity** — `[[architecture#Signals\|signal patterns]]` reads better
3. **Link to headers when specific** — `[[mechanics#Temperature]]` not just `[[mechanics]]`
4. **Backlink when capturing ideas** — link new notes back to source docs

### Common Patterns in Output

```markdown
# Good examples
Per [[mechanics#Temperature System]], the range is...
See [[GDD#Core Loop]] for design rationale.
Related: [[roadmap]], [[architecture]]
- Bug affects [[mechanics#Flamethrower|flamethrower]] system

# Avoid
Per mechanics#Temperature System...  (no wikilink)
See [GDD](design/GDD.md)...           (markdown link)
```

---

## Daily Note Naming

```
# Format: DDMonYYYY.md
27Jan2026.md
03Feb2026.md
```

This format is sort-friendly when listed alphabetically by month within year, and avoids ambiguity between US and EU date orderings.

---

## Error Handling

### Vault Inaccessible

Vaults may be unavailable due to sync issues or path problems.

**When vault is inaccessible:**

1. Report the specific error to user
2. Check for path issues (emoji in folder names, sync conflict files)
3. If still failing, output content to chat instead of file
4. Suggest user check syncthing / iCloud / sync status

### Path with Emoji/Spaces

Always quote paths containing emoji or spaces:

```bash
# Good
cat "${NOTES_ROOT}/personal/daily/06Mar2026.md"
cat "${NOTES_ROOT}/work/Agent 🤖/PR Reviews/note.md"
```

---

## Cross-Vault Considerations

Users can have multiple vaults. **Do not create wikilinks between vaults** — wikilinks only resolve within a single vault.

If referencing content from another vault:

- Quote the content inline
- Note the source vault for context
- Don't use `[[link]]` syntax for cross-vault references

---

## Frontmatter Pattern

```markdown
---
created: {YYYY-MM-DD}
tags: [tag1, tag2]
related: [[Note1]], [[Note2]]
---

# Note Title

Content...
```

Common tag conventions:

| Pattern | Purpose | Examples |
|---------|---------|----------|
| `#area/{domain}` | Domain/topic area | `#area/authentication`, `#area/pricing` |
| `#status/{state}` | Current state | `#status/active`, `#status/blocked`, `#status/complete` |
| `#type/{kind}` | Note type | `#type/exploration`, `#type/decision`, `#type/question` |
| `#project/{name}` | Project association | `#project/{slug}` |
| `#ticket/{id}` | Ticket reference | `#ticket/ABC-123` |

Place tags in frontmatter when possible; in-body tags sparingly for key concepts.
