#!/usr/bin/env python3
"""Lint frontmatter for Athena Notes agents and skills.

Rules:
  Agents (plugins/athena-notes/agents/*.md, plugins/athena-notes/examples/agents/*.md)
    - Frontmatter block present, valid YAML mapping.
    - Required string keys: name, description, tools, model.
    - name matches ^[a-z][a-z0-9-]*$.
    - tools is a comma-separated string of capitalized tool names (not a YAML list).
    - model is one of {opus, sonnet, haiku, inherit}.

  Skills (plugins/athena-notes/skills/*/SKILL.md, plugins/athena-notes/examples/skills/*/SKILL.md)
    - SKILL.md present in each skill directory.
    - Frontmatter block present, valid YAML mapping.
    - Required string keys: name, description.
    - name matches ^[a-z][a-z0-9-]*$.

  Cross-references (main tree only, excludes examples/)
    - Backtick-wrapped slugs in agent/skill bodies — when the literal word "skill"
      or "skills" is adjacent (either form: `<name>` skill  OR  skill: `<name>`) —
      must resolve to a known skill name.
    - Examples are meant to be copied into user projects with their own skill sets,
      so we don't enforce resolution there. Frontmatter is still validated.

Emits GitHub Actions error annotations and exits non-zero on any failure.
"""

from __future__ import annotations

import pathlib
import re
import sys

import yaml

# Anchor to repo root via script location so `python3 scripts/lint-frontmatter.py`
# works from any CWD. Silent "0 files found" passes would be a false-green otherwise.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "athena-notes"
EXAMPLES_ROOT = PLUGIN_ROOT / "examples"

AGENT_DIRS = [
    PLUGIN_ROOT / "agents",
    EXAMPLES_ROOT / "agents",
]

SKILL_DIRS = [
    PLUGIN_ROOT / "skills",
    EXAMPLES_ROOT / "skills",
]

VALID_MODELS = {"opus", "sonnet", "haiku", "inherit"}
SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
TOOLS_RE = re.compile(r"^[A-Z][A-Za-z0-9, ]*$")

# Two tight patterns for skill references in prose:
#   A) `<name>` skill   |  `<name>` skills  |  `<name>` skill's
#   B) skill: `<name>`  |  skills: `<name>`
# Anything looser catches CLI invocations (`via `gh``, `invoke the `tool` agent`).
REF_RE_TRAILING = re.compile(r"`([a-z][a-z0-9-]*)`\s+skill(?:s|'s)?\b")
REF_RE_LEADING = re.compile(r"\bskills?\s*:\s*`([a-z][a-z0-9-]*)`")

_errors = 0


def report(path: pathlib.Path, line: int | None, msg: str) -> None:
    global _errors
    _errors += 1
    # Annotations need paths relative to repo root, not absolute.
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        rel = path
    loc = f"file={rel}"
    if line is not None:
        loc += f",line={line}"
    print(f"::error {loc}::{msg}")


def is_example(path: pathlib.Path) -> bool:
    try:
        path.resolve().relative_to(EXAMPLES_ROOT)
        return True
    except ValueError:
        return False


def parse_frontmatter(path: pathlib.Path) -> tuple[dict | None, str, int]:
    text = path.read_text()
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        report(path, 1, "Missing frontmatter (file must start with '---').")
        return None, "", 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        report(path, 1, "Unterminated frontmatter (no closing '---').")
        return None, "", 0
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as e:
        report(path, 1, f"Invalid YAML in frontmatter: {e}")
        return None, "", 0
    if not isinstance(data, dict):
        report(path, 1, "Frontmatter must be a YAML mapping.")
        return None, "", 0
    body = "\n".join(lines[end + 1 :])
    return data, body, end + 2


def check_string_field(path: pathlib.Path, fm: dict, key: str) -> bool:
    if key not in fm:
        report(path, 1, f"Missing required frontmatter key '{key}'.")
        return False
    value = fm[key]
    if not isinstance(value, str):
        report(
            path,
            1,
            f"Frontmatter key '{key}' must be a string, got {type(value).__name__}."
            + (" (Did you use a YAML list? Use a comma-separated string instead.)" if key == "tools" else ""),
        )
        return False
    if not value.strip():
        report(path, 1, f"Frontmatter key '{key}' must be non-empty.")
        return False
    return True


def lint_agent(path: pathlib.Path) -> tuple[str | None, str, int]:
    fm, body, body_start = parse_frontmatter(path)
    if fm is None:
        return None, "", 0
    for key in ("name", "description", "tools", "model"):
        check_string_field(path, fm, key)
    name = fm.get("name") if isinstance(fm.get("name"), str) else None
    if name and not SLUG_RE.match(name):
        report(path, 1, f"'name' must be lowercase-hyphenated (e.g., 'my-agent'), got {name!r}.")
    tools = fm.get("tools")
    if isinstance(tools, str) and not TOOLS_RE.match(tools.strip()):
        report(path, 1, f"'tools' must be a comma-separated string of capitalized tool names, got {tools!r}.")
    model = fm.get("model")
    if isinstance(model, str) and model not in VALID_MODELS:
        report(path, 1, f"'model' must be one of {sorted(VALID_MODELS)}, got {model!r}.")
    return name, body, body_start


def lint_skill(skill_md: pathlib.Path) -> tuple[str | None, str, int]:
    fm, body, body_start = parse_frontmatter(skill_md)
    if fm is None:
        return None, "", 0
    for key in ("name", "description"):
        check_string_field(skill_md, fm, key)
    name = fm.get("name") if isinstance(fm.get("name"), str) else None
    if name and not SLUG_RE.match(name):
        report(skill_md, 1, f"'name' must be lowercase-hyphenated, got {name!r}.")
    return name, body, body_start


def check_cross_refs(path: pathlib.Path, body: str, body_start: int, known_skills: set[str]) -> None:
    for offset, line in enumerate(body.split("\n")):
        for pattern in (REF_RE_TRAILING, REF_RE_LEADING):
            for m in pattern.finditer(line):
                slug = m.group(1)
                if slug in known_skills:
                    continue
                report(
                    path,
                    body_start + offset,
                    f"Reference to `{slug}` does not resolve to a known skill. "
                    f"Known: {sorted(known_skills)}.",
                )


def main() -> int:
    agent_paths: list[pathlib.Path] = []
    for d in AGENT_DIRS:
        if d.is_dir():
            agent_paths.extend(sorted(d.glob("*.md")))

    skill_mds: list[pathlib.Path] = []
    for d in SKILL_DIRS:
        if not d.is_dir():
            continue
        for sub in sorted(d.iterdir()):
            if not sub.is_dir():
                continue
            skill_md = sub / "SKILL.md"
            if skill_md.is_file():
                skill_mds.append(skill_md)
            else:
                report(skill_md, None, "Skill directory missing SKILL.md.")

    if not agent_paths and not skill_mds:
        # Misconfigured run — the plugin tree is in this repo, so zero-files means
        # the anchor broke (e.g., moved PLUGIN_ROOT). Surface it instead of exiting 0.
        report(PLUGIN_ROOT, None, "No agents or skills discovered — check PLUGIN_ROOT.")
        return 1

    skill_names: set[str] = set()
    skill_bodies: list[tuple[pathlib.Path, str, int]] = []
    for skill_md in skill_mds:
        name, body, _body_start = lint_skill(skill_md)
        # Only main-tree skills populate the known-names set — examples can claim
        # any name, and shouldn't let typos masquerade as valid targets.
        if name and not is_example(skill_md):
            skill_names.add(name)
        if body:
            skill_bodies.append((skill_md, body, _body_start))

    agent_bodies: list[tuple[pathlib.Path, str, int]] = []
    for agent in agent_paths:
        _, body, body_start = lint_agent(agent)
        if body:
            agent_bodies.append((agent, body, body_start))

    for path, body, body_start in agent_bodies + skill_bodies:
        if is_example(path):
            continue
        check_cross_refs(path, body, body_start, skill_names)

    if _errors:
        print(f"\nfrontmatter-lint: {_errors} error(s).", file=sys.stderr)
        return 1
    print(
        f"frontmatter-lint: OK — {len(agent_paths)} agent(s), {len(skill_mds)} skill(s) validated.",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
