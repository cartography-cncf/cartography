# Syft Schema

## Nodes

### SyftPackage

Package nodes created from Syft's `artifacts` array.

Label: `SyftPackage`

| Property | Type | Description |
|----------|------|-------------|
| **`id`** | string | Normalized package ID (e.g., `npm\|express\|4.18.2`) |
| `name` | string | Package name |
| `version` | string | Package version |
| `type` | string | Package type (e.g., `npm`, `pypi`, `deb`) |
| `purl` | string | Package URL |
| **`normalized_id`** | string | Same as `id`; indexed for cross-tool matching |
| `language` | string | Programming language |
| `found_by` | string | Syft cataloger that discovered the package |
| `lastupdated` | int | Timestamp of last update |

## Relationships

### SyftPackage DEPENDS_ON SyftPackage

Self-referential dependency relationships between SyftPackage nodes.

```
(:SyftPackage)-[:DEPENDS_ON]->(:SyftPackage)
```

| Property | Type | Description |
|----------|------|-------------|
| `lastupdated` | int | Timestamp of last update |

Direction: Parent package DEPENDS_ON its dependency (child package).

## Direct vs Transitive Dependencies

Direct and transitive dependencies are determined by graph structure rather than stored properties:

- **Direct dependencies**: Packages with no incoming `DEPENDS_ON` edges (nothing depends on them)
- **Transitive dependencies**: Packages that have incoming `DEPENDS_ON` edges

### Query to find direct dependencies

```cypher
MATCH (p:SyftPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```

### Query to find transitive dependencies

```cypher
MATCH (p:SyftPackage)
WHERE exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```

## Example Graph

```
(express:SyftPackage)  <-- direct (nothing depends on it)
    -[:DEPENDS_ON]->
        (body-parser:SyftPackage)  <-- transitive (express depends on it)
            -[:DEPENDS_ON]->
                (bytes:SyftPackage)  <-- transitive (body-parser depends on it)
```
