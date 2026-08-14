# Orca Security

```{toctree}
config
schema
```

Cartography ingests Orca Security organizations, cloud assets, alerts, and
vulnerability findings. Organizations use the shared `Tenant` ontology label;
alerts use `SecurityIssue`; and vulnerability findings use `CVE`.

Each organization owns its imported resources through `RESOURCE`
relationships. Alerts and vulnerability findings connect directly to affected
assets through `AFFECTS`, allowing findings to be traversed in the context of
Orca's inventory.

Alert relationships are created only when Orca returns a related
`Inventory.id`. Vulnerability relationships use the organization-scoped
`AssetUniqueId` shared by Orca's Inventory and VulnerabilityV2 responses. The
module never correlates findings by resource name, IP address, or another fuzzy
attribute.
