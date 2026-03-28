## Sentry Configuration

Follow these steps to analyze Sentry objects with Cartography.

1. Create an [Internal Integration](https://docs.sentry.io/organization/integrations/integration-platform/internal-integration/) in your Sentry organization.
    1. Go to **Settings** > **Developer Settings** > **Custom Integrations** > **Create New Integration**.
    1. Select **Internal Integration**.
    1. Grant the integration the following scopes: `org:read`, `member:read`, `project:read`, `project:releases`, `alerts:read`, `team:read`.
    1. Save and copy the generated token.
    1. Populate an environment variable with the token.

1. Run Cartography with the following options:

   ```bash
   cartography --sentry-token-env-var SENTRY_TOKEN --sentry-org your-org-slug
   ```

   - `--sentry-token-env-var`: Environment variable name containing the internal integration token.
   - `--sentry-org`: Your Sentry organization slug (visible in the URL: `https://sentry.io/organizations/<slug>/`).
   - `--sentry-host` (optional): Sentry host URL for self-hosted instances (default: `https://sentry.io`).
