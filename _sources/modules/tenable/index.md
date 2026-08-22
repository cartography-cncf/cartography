# Tenable

The Tenable module ingests assets and vulnerability findings from the
[Tenable Export API](https://developer.tenable.com/reference/export-assets-v2).
It uses the asynchronous bulk export workflow to retrieve assets and findings,
then models related networks, cloud details, sources, tags, plugins, and scans.

Tenable findings with CVE identifiers also use the `CVE` ontology label so
Cartography's CVE metadata can enrich them. Tenable asset tags use the shared
`Tag` label and the `TAGGED` relationship. The deprecated `HAS_TAG`
compatibility edge is still written in parallel and will be removed in v1.0.0.

See [configuration](config.md) for connection and scoping options, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
