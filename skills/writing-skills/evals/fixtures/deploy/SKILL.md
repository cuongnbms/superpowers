---
name: deploy
description: Use this skill whenever the user mentions deploy, deployment, release, CI, CD, pipeline, GitHub Actions, build, staging, production, or shipping code. If in doubt, use it.
---

# Deploy

Deploys the current branch to staging or production via `./scripts/deploy.sh <env>`.

1. Confirm the target environment with the user.
2. Run `./scripts/deploy.sh staging` first, then smoke test.
3. Only run `./scripts/deploy.sh production` after staging passes.
