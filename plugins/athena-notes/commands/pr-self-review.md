---
description: Iterative self-review loop for PRs you authored. Runs the three-lens parallel review (correctness/security/simplicity), pre-feeds reviewers with related open issues and .notes/ decisions so overlaps surface as defer-able, and triages each finding through accept/push-back/issue/skip. Loops until the diff is clean or you say done.
---

Invoke the `pr-self-review` skill.

Optional input: a PR URL (`https://github.com/{owner}/{repo}/pull/{N}` or the Forgejo equivalent). Without an argument, the skill infers the PR from the current branch via `gh pr view`.

Arguments: $ARGUMENTS
