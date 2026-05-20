## Summary

<!-- What changed and why. 1-3 sentences or bullets. -->

## Test plan

<!-- How you verified this works. -->
- [ ]

## Changelog

<!-- Pick one. Remove the other. See plugins/cairn-notes/AGENTS.md "Changelog-first, release-on-bump". -->

- [ ] **Non-release PR** — added a bullet under `## [Unreleased]` in `CHANGELOG.md`.
- [ ] **Release PR (`vX.Y.Z`)** — bumped `plugins/cairn-notes/.claude-plugin/plugin.json`, promoted `[Unreleased]` under `## [X.Y.Z] — YYYY-MM-DD`, added the `[X.Y.Z]: .../releases/tag/vX.Y.Z` footer, and retargeted `[Unreleased]` to `compare/vX.Y.Z...HEAD`.
  - [ ] **After merge:** `gh release create vX.Y.Z --target <merge-sha> --title "vX.Y.Z — <summary>"` — otherwise the footer link 404s.
- [ ] **Exempt** — only touched docs, `.github/`, `LICENSE`, or `CHANGELOG.md` itself.
