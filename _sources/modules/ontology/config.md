# Ontology Configuration

The ontology module requires no credentials or module-specific configuration.

## Configure Cartography

You can restrict creation of canonical ontology nodes to selected source modules:

- `--ontology-users-source`: Comma-separated modules that may create canonical `User` nodes. Identity providers such as `okta,duo` are typical sources.
- `--ontology-devices-source`: Comma-separated modules that may create canonical `Device` nodes. Device inventory providers such as `jamf,tailscale` are typical sources.

When a source list is set, data from other modules can link to existing canonical nodes but cannot create those nodes.

## Run Cartography

Run the provider modules together with ontology so the source data is available:

```bash
cartography \
  --selected-modules okta,duo,jamf,tailscale,ontology \
  --ontology-users-source okta,duo \
  --ontology-devices-source jamf,tailscale
```
