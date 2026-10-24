# Jamf

The Jamf module ingests computer, mobile device, and group inventory from a
Jamf Pro tenant. The configured Jamf base URI identifies the tenant and scopes
all loaded resources.

Jamf computer and mobile device records contribute data to canonical ontology
`Device` nodes. Serial number is the primary identity signal. Computers can
also use hostname as a supplemental match when both the Jamf and canonical
hostnames are unique.

See [configuration](config.md) for connection and ontology setup, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
