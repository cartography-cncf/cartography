# Orca Security

```{toctree}
config
schema
```

Cartography ingests Orca alerts and per-target CVE findings. Organizations,
alerts, and vulnerability findings use the `Tenant`, `SecurityIssue`, and `CVE`
ontology labels.

The module retains exact Orca and provider target identifiers as finding
properties. It doesn't ingest Orca Inventory or create asset relationships.
