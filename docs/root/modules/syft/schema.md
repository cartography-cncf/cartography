# Syft Schema

## Relationships

### DEPENDS_ON

Created between TrivyPackage nodes to represent dependency relationships.

```
(:TrivyPackage)-[:DEPENDS_ON]->(:TrivyPackage)
```

| Property | Type | Description |
|----------|------|-------------|
| `lastupdated` | int | Timestamp of last update |
| `_sub_resource_label` | string | Sub-resource label for cleanup scoping |
| `_sub_resource_id` | string | Sub-resource ID for cleanup scoping |

Direction: Parent package DEPENDS_ON its dependency (child package).

## Direct vs Transitive Dependencies

Direct and transitive dependencies are determined by graph structure rather than stored properties:

- **Direct dependencies**: Packages with no incoming `DEPENDS_ON` edges (nothing depends on them)
- **Transitive dependencies**: Packages that have incoming `DEPENDS_ON` edges

### Query to find direct dependencies

```cypher
MATCH (p:TrivyPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```

### Query to find transitive dependencies

```cypher
MATCH (p:TrivyPackage)
WHERE exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```

## Example Graph

```
(express:TrivyPackage)  <-- direct (nothing depends on it)
    -[:DEPENDS_ON]->
        (body-parser:TrivyPackage)  <-- transitive (express depends on it)
            -[:DEPENDS_ON]->
                (bytes:TrivyPackage)  <-- transitive (body-parser depends on it)
```

## Integration with Trivy

The Syft module enriches the graph created by Trivy:

```
                    ┌─────────────────┐
                    │ TrivyImageFinding│
                    │   (CVE-XXXX)    │
                    └────────┬────────┘
                             │ AFFECTS
                             ▼
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ECRImage    │◄───│  TrivyPackage   │───►│   TrivyFix      │
│             │    │  (transitive)   │    │                 │
└─────────────┘    └────────▲────────┘    └─────────────────┘
                            │ DEPENDS_ON
                   ┌────────┴────────┐
                   │  TrivyPackage   │
                   │    (direct)     │
                   └─────────────────┘
```
