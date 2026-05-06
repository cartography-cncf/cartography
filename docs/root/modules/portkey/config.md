## Portkey Configuration

Follow these steps to analyze Portkey resources with Cartography.

1. Create a Portkey Admin API key with read access to the organization control plane.
1. Populate an environment variable with that API key and pass the variable name via `--portkey-apikey-env-var`.
1. Pass your Portkey organization ID via `--portkey-org-id`.
1. If needed, override the API base URL with `--portkey-base-url`. The default is `https://api.portkey.ai/v1`.
