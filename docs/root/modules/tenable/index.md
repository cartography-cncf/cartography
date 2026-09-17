# Tenable

The Tenable module ingests assets and vulnerability findings from the
[Tenable Export API](https://developer.tenable.com/reference/export-assets-v2).
It uses the asynchronous bulk export workflow to retrieve assets and findings,
then models related networks, cloud details, sources, tags, plugins, and scans.

The `TenableTenant` node uses the shared `Tenant` ontology label. Each CVE named by
a plugin becomes a `TenableCve` node carrying the `CVE` ontology label, and both
`TenableFinding` and `TenablePlugin` point at them over `HAS_CVE`. Tenable asset tags
use the shared `Tag` label and the `TAGGED` relationship. The deprecated `HAS_TAG`
compatibility edge is still written in parallel and will be removed in v1.0.0.

Tenable's export names CVEs as bare identifiers and carries no per-CVE scoring of its
own — a plugin's severity is Tenable's own aggregate over every CVE that plugin
covers, so it cannot be attributed back to a single CVE. A CVE's own CVSS data comes
from the canonical record ingested by the [cve](../cve/index.md) module, reached over
`LINKED_TO`:

    MATCH (:TenableCve {cve_id: 'CVE-2026-12345'})<-[:HAS_CVE]-(f:TenableFinding)
    RETURN f

    // ... with the CVE's own severity
    MATCH (f:TenableFinding)-[:HAS_CVE]->(:TenableCve)-[:LINKED_TO]->(c:CVE)
    RETURN f.id, f.severity AS detection_severity, c.base_severity AS cve_severity

`TenableCve.id` is prefixed with `TNB|` (for example `TNB|CVE-2026-12345`) so these
nodes stay distinct from the canonical `(:CVE {id: 'CVE-2026-12345'})` records, which
are separately owned and separately cleaned up. Match on `cve_id` for the bare
identifier. This mirrors the `USV|` prefix the Ubuntu module uses.

```{note}
Before v0.142.0 the CVE identifiers were reachable only through a `cve_list` array
property, which was indexed on `TenableFinding`. Neo4j keys a list property under a
single index entry and rejects values over ~8 KB, so a plugin for a cumulative OS
update naming hundreds of CVEs failed the whole sync. `TenableFinding` also carried
the `CVE` label itself, which exposed just the first CVE to the ontology.

`cve_list` is still written on both nodes for backwards compatibility, but it is no
longer indexed and a predicate like `'CVE-2026-12345' IN f.cve_list` is a label scan
(a range index on a list can only answer whole-array equality, so it never served
that query). Use `HAS_CVE` instead.
```

See [configuration](config.md) for connection and scoping options, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
