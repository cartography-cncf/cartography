# Unikraft Configuration

Follow these steps to analyze Unikraft Cloud infrastructure in Cartography.

## Prerequisites

A Unikraft Cloud account with at least one API token. See
[Unikraft's API documentation](https://docs.unikraft.com/api/platform/v1)
for how the platform API is organized.

## Authentication

Generate a Unikraft Cloud API token from the Unikraft Cloud console and
store it in an environment variable, e.g. `UNIKRAFT_TOKEN`.

## Configure Cartography

- `--unikraft-token-env-var`: Name of the environment variable containing
  your Unikraft Cloud API token. Required to enable this module.

## Run Cartography

```bash
UNIKRAFT_TOKEN=<your-token> cartography --unikraft-token-env-var UNIKRAFT_TOKEN
```

## Advanced Configuration

Unikraft Cloud is organized into five metros (`fra`, `dal`, `sin`, `was`,
`sfo`), each with its own base URL. There is no API endpoint that lists
available metros, so Cartography queries all five on every sync and records
which metro each resource (`UnikraftInstance`, `UnikraftVolume`,
`UnikraftServiceGroup`, `UnikraftCertificate`, `UnikraftImage`) was observed
in via its `metro` property. Requests retry with backoff on rate limiting and
server errors, but a metro that stays unreachable through those retries fails
the sync rather than being skipped: since cleanup is scoped to the account as
a whole rather than per metro, silently skipping a metro would let its
resources be deleted from the graph as if they no longer existed.

The `UnikraftAccount` node is identified by the UUID returned from the
metro-independent `/v1/users/quotas` endpoint, so no account identifier needs
to be configured manually.

## References

- [Unikraft Cloud Platform API](https://docs.unikraft.com/api/platform/v1)
