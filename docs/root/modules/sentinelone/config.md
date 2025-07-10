## SentinelOne Configuration

Follow these steps to analyze SentinelOne objects with Cartography.

1. Prepare a SentinelOne API token with appropriate permissions.
1. Pass the SentinelOne API URL to the `--sentinelone-api-url` CLI arg.
1. Populate an environment variable with the API token.
1. Pass that environment variable name to the `--sentinelone-api-token-env-var` CLI arg.
1. Optionally, pass specific account IDs to sync using the `--sentinelone-account-ids` CLI arg (comma-separated).

## Required Permissions

The API token requires the following permissions:
- **Account** - Read access to account information
- **Agent** - Read access to agent information
