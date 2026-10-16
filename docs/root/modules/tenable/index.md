# Tenable

The Tenable module ingests assets and vulnerability findings from the
[Tenable Export API](https://developer.tenable.com/reference/export-assets-v2).
It uses the asynchronous bulk export workflow to retrieve assets and findings,
then models related networks, cloud details, sources, tags, plugins, and scans.

The `TenableTenant` node uses the shared `Tenant` ontology label. Tenable asset tags
use the shared `Tag` label and the `TAGGED` relationship. The deprecated `HAS_TAG`
compatibility edge is still written in parallel and will be removed in v1.0.0.

## CVEs

Each CVE named by a plugin becomes a `TenableCve` node carrying the `CVE` ontology
label. A finding reaches its CVEs through the plugin that detected it:

    (:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)-[:HAS_CVE]->(:TenableCve:CVE)

Findings have no `HAS_CVE` edge of their own. A plugin for a cumulative OS update names
hundreds of CVEs and is reported once per affected host, so an edge from every finding
would multiply by the size of the fleet.

To find findings by CVE:

    MATCH (:TenableCve {cve_id: 'CVE-2026-12345'})<-[:HAS_CVE]-(:TenablePlugin)
          <-[:DETECTED_BY]-(f:TenableFinding)
    RETURN f

Tenable's export names CVEs as bare identifiers with no per-CVE scoring, and a plugin's
severity is Tenable's roll-up over every CVE it covers. So `TenableCve` has no
`_ont_base_severity` or `_ont_vuln_status`, and a query that filters `CVE` nodes on
those fields will not return Tenable data. This differs from most scanner modules, which
put the `CVE` label on the finding; Tenable puts it on the vulnerability record, like the
`cve` and Ubuntu modules. Detection severity and state are `TenableFinding.severity` and
`TenableFinding.state`.

The `CVE` label gives every `TenableCve` an `_ont_cve_id`, which lines it up with other
providers' records of the same CVE, including the NVD data from the
[cve](../cve/index.md) module. To read a CVE's own severity:

    MATCH (f:TenableFinding)-[:DETECTED_BY]->(:TenablePlugin)-[:HAS_CVE]->(t:TenableCve)
    MATCH (n:CVE {_ont_cve_id: t._ont_cve_id, _ont_source: 'cve'})
    RETURN f.id, t.cve_id, f.severity AS detection_severity,
           n._ont_base_severity AS cve_severity

`TenableCve.id` is `TNB|<tenant id>|<CVE ID>`, for example
`TNB|cloud.tenable.com|CVE-2026-12345`. Match on `cve_id` for the bare identifier.

## Upgrading from an earlier version

Earlier versions put the `CVE` label on `TenableFinding` and kept each finding's CVE IDs
in an indexed `TenableFinding.cve_list`. A plugin naming enough CVEs made that index
reject the write and fail the whole sync. This version no longer writes the property, so
the sync succeeds even while the old index exists, and every sync removes the legacy
`CVE` label, `_ont_*` fields and `cve_list` from findings that carried the label.

Two leftovers do no harm and can be removed once, by hand. Do not run these before
upgrading: an earlier version recreates both on every sync.

The now-unused index. Find its name:

    SHOW INDEXES YIELD name, type, labelsOrTypes, properties
    WHERE type = 'RANGE' AND labelsOrTypes = ['TenableFinding'] AND properties = ['cve_list']
    RETURN name

and drop it:

    DROP INDEX `<name>` IF EXISTS

Findings without CVEs never carried the label, but still hold `_ont_*` fields and an
empty `cve_list`. Run this until it returns 0:

    MATCH (f:TenableFinding)
    WHERE f._ont_source IS NOT NULL OR f.cve_list IS NOT NULL
    WITH f LIMIT 10000
    REMOVE f._ont_source, f._ont_cve_id, f._ont_base_severity, f._ont_vuln_status,
           f.cve_list
    RETURN count(f) AS removed

To look up findings by CVE, replace `'CVE-2026-12345' IN f.cve_list` with the
`HAS_CVE` query above. `TenablePlugin.cve_list` still lists a plugin's CVEs.

See [configuration](config.md) for connection and scoping options, and the
generated [schema](schema.md) for fields and relationships.

```{toctree}
config
schema
```
