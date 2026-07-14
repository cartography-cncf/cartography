# SentinelOne

The SentinelOne module ingests accounts, endpoint agents, application
inventory, installed application versions, and application vulnerability
findings. Data can be synced by account or by site for site-scoped MSSP
deployments.

SentinelOne accounts participate in the ontology as tenants, and application
findings participate in cross-tool vulnerability queries. Agent records can
also contribute data to canonical ontology `Device` nodes by matching endpoint
serial numbers.

See [configuration](config.md) for connection, scoping, and ontology setup, and
the generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
