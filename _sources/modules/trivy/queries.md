# Trivy Queries

## Compare a finding's rating across images

```cypher
MATCH (f:TrivyImageFinding {cve_id: 'CVE-2026-27171'})-[r:AFFECTS]->(img:Image)
RETURN img.`_ont_digest`, r.severity, r.severity_source, r.status
```

## Find the files that contain a vulnerable package

```cypher
MATCH (f:TrivyImageFinding {cve_id: 'CVE-2023-24538'})-[:AFFECTS]->(p:TrivyPackage)
      -[d:DEPLOYED]->(target)
WHERE target:Image OR target:FilesystemSnapshot
RETURN p.name, p.version, target.id, d.locations
```
