## Sentry Configuration

Follow these steps to analyze Sentry objects with Cartography.

1. Create an [Internal Integration](https://docs.sentry.io/organization/integrations/integration-platform/internal-integration/) in your Sentry organization.
    1. Go to **Settings** > **Developer Settings** > **Custom Integrations** > **Create New Integration**.
    1. Select **Internal Integration**.
    1. Grant the integration the following scopes: `org:read`, `member:read`, `project:read`, `project:releases`, `alerts:read`, `team:read`.
    1. Save and copy the generated token.
    1. Populate an environment variable with the token. You can pass the environment variable name via CLI with the `--sentry-token-env-var` parameter.

1. (Optional) If you are using a self-hosted Sentry instance, set the `--sentry-host` parameter to your instance URL (e.g., `https://sentry.example.com`). The default is `https://sentry.io`.
