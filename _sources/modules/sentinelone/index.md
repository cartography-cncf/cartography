# SentinelOne

The SentinelOne module ingests accounts, endpoint agents, application
inventory, installed application versions, and application vulnerability
findings. Data can be synced by account or by site for site-scoped MSSP
deployments.

SentinelOne accounts participate in the ontology as tenants, and application
findings participate in cross-tool vulnerability queries. Agent records can
also contribute data to canonical ontology `Device` nodes by matching endpoint
serial numbers.

## Site-scoped ingestion

When a site-scoped token cannot call the SentinelOne accounts endpoint,
Cartography enumerates the sites visible to the token. It synthesizes
`S1Account` nodes from parent account metadata in each site response and
attaches site resources to those accounts.

When the sync is explicitly limited with `--sentinelone-site-ids`, Cartography
skips account-wide cleanup so data from sibling sites under the same account is
not deleted.

See [configuration](config.md) for connection, scoping, and ontology setup, and
the generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
