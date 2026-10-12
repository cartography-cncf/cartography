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
own. A plugin's severity is Tenable's own roll-up over every CVE that plugin covers,
so it cannot be attributed back to a single CVE. Per-detection severity and state stay
on `TenableFinding`.

To find findings by CVE:

    MATCH (:TenableCve {cve_id: 'CVE-2026-12345'})<-[:HAS_CVE]-(f:TenableFinding)
    RETURN f

The `CVE` label gives every `TenableCve` an `_ont_cve_id`. That is how it lines up with
other providers' records of the same CVE, including the NVD data from the
[cve](../cve/index.md) module. To read a CVE's own severity:

    MATCH (f:TenableFinding)-[:HAS_CVE]->(t:TenableCve)
    MATCH (n:CVE {_ont_cve_id: t._ont_cve_id, _ont_source: 'cve'})
    RETURN f.id, f.severity AS detection_severity, n._ont_base_severity AS cve_severity

Most scanner modules put the `CVE` label on the finding. Tenable puts it on the
vulnerability record instead, like the `cve` and Ubuntu modules. Because Tenable's
export does not score individual CVEs, `TenableCve` has no `_ont_base_severity` or
`_ont_vuln_status`, and a query that filters `CVE` nodes on those fields will not
return Tenable data. Use `TenableFinding.severity` and `TenableFinding.state` instead.

`TenableCve.id` is prefixed with `TNB|` (for example `TNB|CVE-2026-12345`). The `cve`
module merges its records on `(:CVE {id})`, so a bare id would make it adopt
`TenableCve` nodes as its own. Match on `cve_id` for the bare identifier. This mirrors
the `USV|` prefix the Ubuntu module uses.

```{note}
In earlier versions `TenableFinding` kept its CVE IDs in an indexed `cve_list` array
property, and `cve_id` held only the first one. Neo4j keys a list property under a
single index entry and rejects values over ~8 KB, so a plugin for a cumulative OS
update naming hundreds of CVEs failed the whole sync. `TenableFinding` also carried
the `CVE` label itself.

`cve_list` is still written on both nodes for backwards compatibility, but it is no
longer indexed, so a predicate like `'CVE-2026-12345' IN f.cve_list` is a label scan
(a range index on a list only answers whole-array equality, so it never served that
query). Use `HAS_CVE` instead.
```

## Upgrading from an earlier version

Cartography never removes an index, label or property it no longer declares, so a
graph synced by an earlier version keeps two things this version no longer uses.
Remove them once, after upgrading: an earlier version recreates both on every sync.

First, drop the old `cve_list` index. `cve_list` is still written, so while the index
exists a large CVE list still fails the sync. Find its name:

    SHOW INDEXES YIELD name, type, labelsOrTypes, properties
    WHERE type = 'RANGE' AND labelsOrTypes = ['TenableFinding'] AND properties = ['cve_list']
    RETURN name

and drop it:

    DROP INDEX `<name>` IF EXISTS

Then remove the `CVE` label and `_ont_*` properties from `TenableFinding`. Nothing
updates them any more, so they go stale, and `CVE` queries would count Tenable data
twice. Run this until it returns 0:

    MATCH (f:TenableFinding)
    WHERE f:CVE OR f._ont_source = 'tenable'
    WITH f LIMIT 10000
    REMOVE f:CVE, f._ont_source, f._ont_cve_id, f._ont_base_severity, f._ont_vuln_status
    RETURN count(f) AS removed

See [configuration](config.md) for connection and scoping options, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
