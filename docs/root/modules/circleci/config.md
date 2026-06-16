## CircleCI Configuration

Follow these steps to analyze CircleCI objects with Cartography.

1. Prepare your CircleCI personal API token
    1. Create a [personal API token](https://app.circleci.com/settings/user/tokens) in the CircleCI web app.
    1. Populate an environment variable with the token. Pass the environment variable name via CLI with `--circleci-token-env-var`.
1. Optionally override the API base URL with `--circleci-base-url` (default: `https://circleci.com/api/v2`).
1. Optionally sync project-scoped resources by passing a comma-separated list of project slugs via `--circleci-project-slugs` (e.g. `gh/my-org/my-repo,gh/my-org/other-repo`).

### A note on discovery

CircleCI API v2 has no endpoint to list all projects in an organization, so Cartography splits the sync into two tiers:

- **Auto-discovered from the token**: organizations (`/me/collaborations`), the token owner (`/me`), contexts, and context environment variable names.
- **Project-scoped (requires `--circleci-project-slugs`)**: project details, project environment variables, checkout keys, webhooks, schedules, and pipelines.

### A note on secrets

CircleCI never returns secret values through the API. Cartography ingests environment variable **names and metadata only**, never their values.
