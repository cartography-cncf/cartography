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
`UnikraftServiceGroup`, `UnikraftCertificate`) was observed in via its
`metro` property. Requests retry with backoff on rate limiting and server
errors, but a metro that stays unreachable through those retries fails
the sync rather than being skipped: since cleanup is scoped to the account as
a whole rather than per metro, silently skipping a metro would let its
resources be deleted from the graph as if they no longer existed.

The `UnikraftAccount` node is identified by the UUID returned from the
metro-independent `/v1/users/quotas` endpoint, so no account identifier needs
to be configured manually.

Every other resource is identified by its Unikraft-assigned UUID alone,
assumed globally unique across metros (standard UUIDv4 practice). If a UUID
were ever reused across two metros for two different real resources, they
would be merged into a single graph node.

### Images are not ingested

Unikraft images are intentionally not ingested. The platform API docs
describe `GET /v1/images` and `GET /v1/image-store` on the per-metro hosts,
but both 404 on every metro against a real account; the working endpoint
appears to have moved to a separate, undocumented `controlplane.unikraft.cloud`
host with a different response shape. See
[unikraft-cloud/openapi#3](https://github.com/unikraft-cloud/openapi/issues/3)
for details. This will be revisited once that's resolved or confirmed.

### Pagination is not currently supported

The platform API docs describe `count`/`from`/`order`/`sortby` params for
cursor-based pagination on list endpoints, but every variant of them (as
query params, as a JSON body, in either casing) is rejected by the live
API — confirmed directly against a real account. Cartography fetches a
single, unparameterized page per resource type per metro; accounts with
more resources of a given type than a single response returns will not
have everything ingested. See
[unikraft-cloud/openapi#4](https://github.com/unikraft-cloud/openapi/issues/4)
for details. This will be revisited once a working pagination mechanism is
confirmed.

## References

- [Unikraft Cloud Platform API](https://docs.unikraft.com/api/platform/v1)
- [unikraft-cloud/openapi#3](https://github.com/unikraft-cloud/openapi/issues/3) — tracks the images API discrepancy
- [unikraft-cloud/openapi#4](https://github.com/unikraft-cloud/openapi/issues/4) — tracks the pagination and other request-shape discrepancies
