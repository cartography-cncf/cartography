# Debian Security Tracker Queries

## How Debian rates one CVE in each release

```cypher
MATCH (e:DebianSecurityTrackerEntry {cve_id: 'CVE-2005-2541'})
RETURN e.release, e.release_version, e.source_package, e.status, e.urgency,
       e.fixed_version, e.not_affected
ORDER BY e.release
```

## Tracker entries for the Debian findings on each image

This joins [Trivy](../trivy/index.md) findings on Debian images to the entries
for each image's release. Keep to the distribution's own packages with
`p.class_name = 'os-pkgs'`: language packages in the same image carry the
image's `os_family` too. `p.type` does not work for this. The package node is
shared by every image with a package of that name and version, a Debian and an
Ubuntu image included, and holds the type of the last report ingested.

```cypher
MATCH (f:TrivyImageFinding)-[:AFFECTS]->(img:Image)
MATCH (f)-[:AFFECTS]->(p:TrivyPackage)-[d:DEPLOYED]->(img)
WHERE d.os_family = 'debian' AND p.class_name = 'os-pkgs'
MATCH (e:DebianSecurityTrackerEntry {cve_id: f.cve_id, release_version: d.os_release})
RETURN DISTINCT img.`_ont_digest` AS image, f.cve_id AS cve, p.name AS package,
       e.source_package, e.urgency, e.status, e.not_affected
```

```{warning}
The join matches on the CVE and the release, not on the source package, so it
returns one row for each source package the tracker lists the CVE under. A CVE
in widely vendored code can have entries for dozens of source packages, with
different statuses. Do not aggregate `not_affected`, `status` or `urgency`
across the rows of one finding, for example by treating the finding as not
affected when any row is: that row can belong to a source package the image
does not contain. Only the row for the source package that the image's package
was built from applies. Cartography does not record that source package yet:
Trivy reports it as `SrcName` on each entry of a result's `Packages` in its JSON
report, which is the only place to check a row against for now.
```
