# Trivy Queries

## Compare a finding's rating across images

```cypher
MATCH (f:TrivyImageFinding {cve_id: 'CVE-2026-27171'})-[r:AFFECTS]->(img:Image)
RETURN img.`_ont_digest`, r.severity, r.severity_source, r.status
```

## Operating system of each image

Count each image's operating system packages. Only the distribution's own
packages carry the image's OS on `DEPLOYED`:

```cypher
MATCH (p:TrivyPackage)-[d:DEPLOYED]->(img:Image)
WHERE d.os_family IS NOT NULL
RETURN img.`_ont_digest`, d.os_family, d.os_name, d.os_release,
       count(p) AS os_packages
```

To join the findings on Debian images to the Debian security tracker, see the
[Debian security tracker queries](../debian/queries.md).
