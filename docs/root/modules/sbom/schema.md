## SBOM Schema

The SBOM module does not create new node types. Instead, it enriches existing TrivyPackage nodes (created by the [Trivy module](../trivy/schema.md)) with dependency graph information.

### Enrichments to TrivyPackage

The SBOM module adds the following to TrivyPackage nodes:

| Field | Description |
|-------|-------------|
| is_direct | Boolean indicating if this package is a direct dependency (`true`) or transitive dependency (`false`) |

**Note:** Direct dependencies are packages explicitly declared in your project's manifest (e.g., `package.json`, `requirements.txt`). Transitive dependencies are packages pulled in by your direct dependencies.

### DEPENDS_ON Relationship

The SBOM module creates `DEPENDS_ON` relationships between TrivyPackage nodes to represent the dependency graph.

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

After both Trivy and SBOM modules have run, the graph supports queries like:

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
│  is_direct=true │    │  is_direct=false│
└─────────────────┘    └────────┬────────┘
     DEPENDS_ON                 │ DEPENDS_ON
                                ▼
                         ┌─────────────────┐
                         │  TrivyPackage   │
                         │  mime-types     │
                         │  is_direct=false│
                         └─────────────────┘
```

This structure enables the key query: "A CVE affects `accepts` (transitive). Which direct dependency should I update?" Answer: `express`.
