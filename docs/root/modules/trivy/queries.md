# Trivy Queries

## Compare a finding's rating across images

```cypher
MATCH (f:TrivyImageFinding {cve_id: 'CVE-2026-27171'})-[r:AFFECTS]->(img:Image)
RETURN img.`_ont_digest`, r.severity, r.severity_source, r.status
```
