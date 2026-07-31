## Nullify Configuration

Follow these steps to analyze [Nullify](https://nullify.ai) objects with Cartography.

1. Prepare your Nullify service-account token.
    1. In your tenant dashboard (`https://app.<tenant>.nullify.ai`), go to **Configure → Service Accounts** and generate a new service account. Copy the token immediately: it is only shown once.
    1. Populate an environment variable with the token. Pass the environment variable name via CLI with `--nullify-token-env-var`.
1. Provide your tenant slug with `--nullify-tenant` (for example `acme` for `https://api.acme.nullify.ai`). This is required and is used to build the API base URL.
1. Optionally override the API base URL with `--nullify-base-url` (defaults to `https://api.<tenant>.nullify.ai`).

The token is tenant-scoped, so a single service account is sufficient for a whole tenant. Grant it read access to the capabilities you want to ingest (code review, dependencies, secrets, containers, cloud audits).

### A note on secrets

Nullify never returns raw secret values through the API. Secret findings expose only a redacted preview and a hash, and Cartography stores only what the API returns; it never ingests the real secret.
