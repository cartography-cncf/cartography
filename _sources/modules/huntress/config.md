# Huntress Configuration

## Authentication

Cartography authenticates with a Huntress account API key and its secret key,
sent as HTTP basic access authentication.

Generate the pair in the Huntress console at
`https://<your account subdomain>.huntress.io/account/api_credentials`: click
**Setup**, then **Generate**.

Save the secret key immediately. Huntress only displays it during generation, and
you have to regenerate the whole pair if you lose it.

Store both in environment variables:

```bash
export HUNTRESS_API_KEY="<api key>"
export HUNTRESS_API_SECRET="<api secret key>"
```

## Required Permissions

The credential needs read access to the account, organizations, agents, and
incident reports.

## Optional Permissions

Listing memberships requires an additional permission that is not granted to
every API credential. Without it, the API answers `403` and Cartography logs a
warning and skips `HuntressUser` and `HuntressRole`; the rest of the module still
syncs, and users and roles ingested by an earlier authorized run are left in
place rather than deleted.

## Configure Cartography

Pass the names of the environment variables holding the credentials with
`--huntress-api-key-env-var` and `--huntress-api-secret-env-var`. If the flags
are omitted, Cartography falls back to reading `HUNTRESS_API_KEY` and
`HUNTRESS_API_SECRET`. Both halves are required: with only one of them, the
module skips itself.

The account is resolved from the credentials, so there is no tenant flag to set.

## Run Cartography

```bash
cartography \
  --selected-modules huntress \
  --huntress-api-key-env-var HUNTRESS_API_KEY \
  --huntress-api-secret-env-var HUNTRESS_API_SECRET
```

## Advanced Configuration

Huntress agents can contribute to canonical ontology `Device` nodes. To use
Huntress as a device source of truth, include it in `--ontology-devices-source`:

```bash
cartography \
  --selected-modules huntress,ontology \
  --huntress-api-key-env-var HUNTRESS_API_KEY \
  --huntress-api-secret-env-var HUNTRESS_API_SECRET \
  --ontology-devices-source huntress
```

Multiple device sources can be provided as a comma-separated list, for example
`--ontology-devices-source huntress,kandji`.

| Flag | Description |
|---|---|
| `--huntress-api-key-env-var` | Name of the environment variable holding the account API key. Defaults to reading `HUNTRESS_API_KEY`. |
| `--huntress-api-secret-env-var` | Name of the environment variable holding the API secret key. Defaults to reading `HUNTRESS_API_SECRET`. |
| `--huntress-base-uri` | Huntress API base URI. Defaults to `https://api.huntress.io`. |

## Troubleshooting

The Huntress API rate limits each account on a sliding window. Cartography
retries `429` responses with an exponential backoff, so a sync that runs
alongside other API consumers takes longer rather than failing.

## References

- [Huntress API reference](https://api.huntress.io/docs)
- [Huntress API credentials](https://support.huntress.io/hc/en-us/articles/4404005178771-Getting-Started-with-the-Huntress-API)
