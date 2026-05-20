---
description: Plan the workday — pull context from tracked sources, get goals from forge, write the day's plan to the personal vault. Day-of-week adaptive (Mon = week-prep, Fri = week-wrap).
---

Invoke the `workday-planning` skill.

Arguments (all optional):

- `--mode=day` — force daily plan only (no overlays)
- `--mode=week-prep` — force Monday week-prep overlay + day plan
- `--mode=week-wrap` — force Friday week-wrap overlay + day plan
- `--edit-sources` — jump straight to editing `~/.claude/cairn/planning-sources.md`

If no flags are passed, mode auto-detects from the day-of-week in the user's timezone.

Arguments: $ARGUMENTS
