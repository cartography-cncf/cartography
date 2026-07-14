# Socket.dev

The Socket.dev module ingests organizations, monitored repositories,
dependencies, security alerts, and available fixes.

Socket.dev organizations are labeled as ontology `Tenant` nodes. Dependencies
are labeled as `Dependency`, alerts as `Risk` and `SecurityIssue`, and fixes as
`Fix`. Monitored repositories link to matching ontology `CodeRepository` nodes,
and normalized dependency identifiers support cross-tool package matching.

See [configuration](config.md) for token setup and the generated
[schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
