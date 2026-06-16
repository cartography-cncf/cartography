## CircleCI Configuration

Follow these steps to analyze CircleCI objects with Cartography.

1. Prepare your CircleCI personal API token
    1. Create a [personal API token](https://app.circleci.com/settings/user/tokens) in the CircleCI web app.
    1. Populate an environment variable with the token. Pass the environment variable name via CLI with `--circleci-token-env-var`.
1. Optionally override the API base URL with `--circleci-base-url` (default: `https://circleci.com/api/v2`).
1. Optionally add extra project slugs via `--circleci-project-slugs` (comma-separated, e.g. `gh/my-org/my-repo,gh/my-org/other-repo`).

### A note on project discovery

CircleCI API v2 has no endpoint to list all projects in an organization. Cartography discovers projects from each org's pipeline feed (`GET /pipeline?org-slug=...`), which surfaces the recently-built projects the token owner follows (about 250 per org). Projects with no recent pipeline activity will not be auto-discovered: add them explicitly with `--circleci-project-slugs`.

Because this discovery is partial, `CircleCIProject` nodes are upserted but never automatically deleted: a project that drops out of the recent feed is not removed (deleting it would orphan its resources and lose a still-valid project). A project's own sub-resources (env vars, keys, webhooks, etc.) are still cleaned up on each sync, since a synced project is fully enumerated. Stale projects can be identified by an old `lastupdated`.

### A note on secrets

CircleCI never returns secret values in clear text through the API. Context environment variables expose no value at all; project environment variables expose only a masked value (`xxxx` plus the last four characters). Cartography stores what the API returns, never the real secret.
