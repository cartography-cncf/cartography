## SBOM Schema

The SBOM module does not create new node types. Instead, it creates `DEPENDS_ON` relationships between existing TrivyPackage nodes (created by the [Trivy module](../trivy/schema.md)).

### DEPENDS_ON Relationship

The SBOM module creates `DEPENDS_ON` relationships between TrivyPackage nodes to represent the dependency graph from CycloneDX SBOMs (e.g., from Syft).

```
(TrivyPackage)-[DEPENDS_ON]->(TrivyPackage)
```

| Field | Description |
|-------|-------------|
| lastupdated | Timestamp of the last time the relationship was updated |

**Example:** If `express` depends on `accepts`, the graph will contain:

```
(:TrivyPackage {name: 'express'})-[:DEPENDS_ON]->(:TrivyPackage {name: 'accepts'})
```

### Graph Structure After SBOM Enrichment

After both Trivy and SBOM modules have run, the graph supports dependency chain traversal:

```
                    ┌─────────────────┐
                    │ TrivyImageFinding│
                    │ (CVE-2021-1234) │
                    └────────┬────────┘
                             │ AFFECTS
                             ▼
┌─────────────────┐    ┌─────────────────┐
│  TrivyPackage   │───▶│  TrivyPackage   │
│  express        │    │  accepts        │
└─────────────────┘    └────────┬────────┘
     DEPENDS_ON                 │ DEPENDS_ON
                                ▼
                         ┌─────────────────┐
                         │  TrivyPackage   │
                         │  mime-types     │
                         └─────────────────┘
```

### Example Queries

**Find packages that nothing depends on (potential direct dependencies):**

```cypher
MATCH (p:TrivyPackage)
WHERE NOT ()-[:DEPENDS_ON]->(p)
RETURN p.name, p.version
```

**Trace from CVE to upstream packages:**

```cypher
MATCH (cve:TrivyImageFinding)-[:AFFECTS]->(vuln:TrivyPackage)
MATCH (upstream:TrivyPackage)-[:DEPENDS_ON*1..5]->(vuln)
RETURN cve.cve_id, vuln.name AS vulnerable_package,
       upstream.name AS upstream_package
```
