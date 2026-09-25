# Miradore Configuration

## Authentication

Cartography authenticates with a Miradore API key. Create one in the Miradore
web console under *System > Infrastructure diagram*: hover over the API icon,
click **Create key**, and give the key a descriptive name.

Save the key immediately. Miradore does not display it again after creation.

Store it in an environment variable:

```bash
export MIRADORE_API_KEY="<api key>"
```

## Configure Cartography

Set the site name with `--miradore-site-name`. This is the `<site>` segment of
your Miradore URL, `https://online.miradore.com/<site>`, and it is used as the
tenant identifier in the graph.

Pass the name of the environment variable holding the key with
`--miradore-api-key-env-var`. If the flag is omitted, Cartography falls back to
reading `MIRADORE_API_KEY`.

## Run Cartography

```bash
cartography \
  --selected-modules miradore \
  --miradore-site-name mycompany \
  --miradore-api-key-env-var MIRADORE_API_KEY
```

## Advanced Configuration

Miradore records can contribute to canonical ontology `Device` nodes. To use
Miradore as a device source of truth, include it in
`--ontology-devices-source`:

```bash
cartography \
  --selected-modules miradore,ontology \
  --miradore-site-name mycompany \
  --miradore-api-key-env-var MIRADORE_API_KEY \
  --ontology-devices-source miradore
```

Multiple device sources can be provided as a comma-separated list, for example
`--ontology-devices-source miradore,jamf`.

| Flag | Description |
|---|---|
| `--miradore-site-name` | Miradore site name, which identifies the tenant. Required to enable the module. |
| `--miradore-api-key-env-var` | Name of the environment variable holding the API key. Defaults to reading `MIRADORE_API_KEY`. |
| `--miradore-base-uri` | Miradore base URI. Defaults to `https://online.miradore.com`. |

## References

- [Miradore API specification (API v1)](https://www.miradore.com/knowledge/integrations/programmers-guide-to-api-v1/)
- [Getting started with the Miradore API](https://www.miradore.com/knowledge/integrations/getting-started-with-api/)

Miradore also publishes an [API v2](https://www.miradore.com/knowledge/integrations/miradore-api-v2/),
but it exposes no endpoints for listing inventory, so this module uses API v1.
