# Examples

Personal agents and skills Bryan built on top of Athena Notes. They are **reference implementations, not parts of the plugin** — they will not run unless you copy them into your own Claude Code agents/skills directory and adapt them.

## What's here

### `agents/`

| Agent | Purpose | What to adapt |
| --- | --- | --- |
| [calliope.md](agents/calliope.md) | Voice keeper + ship-it coach for blog / newsletter / YouTube content | Replace the SnowboardTechie brand, voice markers, and platform formats with your own. |
| [aria.md](agents/aria.md) | Accessibility reviewer tuned for VA.gov + VADS | Replace VA design system references with your org's design system; adjust WCAG targets. |
| [gamedev.md](agents/gamedev.md) | Godot 4.5 project assistant for the Burnt Ice roguelike | Replace project name, path, engine, and phase list with your own game project. |

### `skills/`

| Skill | Purpose | What to adapt |
| --- | --- | --- |
| [catalog-review](skills/catalog-review/SKILL.md) | Review catalog dependency update PRs with TypeSpec/lockfile/audit awareness | Remove if you don't use TypeSpec or catalog-style monorepos. |
| [manual-merge](skills/manual-merge/SKILL.md) | Guided manual merge workflow for a specific repo layout | Adjust to your branching conventions. |
| [sprint-deliverable-update](skills/sprint-deliverable-update/SKILL.md) | Draft sprint-update comments on HHS-style deliverable issues | Replace HHS deliverable structure with your own ticket/sprint format. |

## How to use an example

1. **Copy, don't symlink.** These files will drift as Bryan evolves them.
   ```bash
   # Agent
   cp plugins/athena-notes/examples/agents/calliope.md ~/.claude/agents/mywriter.md

   # Skill
   cp -r plugins/athena-notes/examples/skills/catalog-review ~/.claude/skills/
   ```

2. **Rename.** The `name:` frontmatter field and any references inside the body should match your new agent/skill name.

3. **Replace hardcoded context.** Search the file for brand names, paths (`~/code/...`, `~/notes/...`), project names, and domain-specific language (e.g., "VA.gov", "Burnt Ice", "SnowboardTechie"). Swap them for yours.

4. **Review tool permissions.** Make sure the `tools:` list matches what your adapted agent actually needs — read-only audit agents should not carry `Write`/`Edit`.

5. **Test it.** Invoke it from Athena (`@mywriter …`) or trigger the skill and verify it does what you expect.

## Contributing back

If you build something general-purpose on top of these examples — e.g., a voice-keeper agent that's not tied to one brand — consider opening a PR to move it into the main `agents/` or `skills/` tree. See [CONTRIBUTING.md](../../../CONTRIBUTING.md).
