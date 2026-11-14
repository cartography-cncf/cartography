# Miradore

The Miradore module ingests device, user, organization, location, tag, and
configuration profile inventory from a Miradore Online tenant. The configured
site name identifies the tenant and scopes all loaded resources.

A single `MiradoreDevice` node type covers every platform Miradore manages
(Android, iOS, macOS, Windows desktop, and Windows Phone), including the
platform-specific security posture Miradore reports: encryption and passcode
state, iOS supervision and jailbreak detection, Android root state and patch
level, macOS Activation Lock, and Windows Secure Boot, antivirus, and firewall
status.

Miradore numbers its items per tenant, so every node is identified in the graph by
`<site name>/<Miradore ID>`. The raw per-tenant identifier is kept alongside as
`miradore_id`, which is what you match on when cross-referencing the Miradore
console.

Miradore device records contribute data to canonical ontology `Device` nodes.
Serial number is the primary identity signal, with hostname used as a
supplemental match when both the Miradore and canonical hostnames are unique.
Miradore user accounts carry the `UserAccount` label, so they are aggregated
into canonical `User` nodes and give devices their `OWNS` ownership edge.

This module uses Miradore API v1, which is the version that supports reading
inventory. API v2 only exposes device actions such as lock, wipe, and reboot.

See [configuration](config.md) for connection and ontology setup, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
