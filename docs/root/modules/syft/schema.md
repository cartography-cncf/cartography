## Syft Schema

### SyftPackage

Representation of a software package discovered by Syft, created from Syft's `artifacts` array.

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Normalized package ID (e.g., `npm\|express\|4.18.2`) |
| name | Package name |
| version | Package version |
| type | Package type (e.g., `npm`, `pypi`, `deb`) |
| purl | Package URL |
| **normalized_id** | Normalized ID for cross-tool matching (format: `{type}\|{namespace/}{name}\|{version}`). Indexed. |
| language | Programming language |
| found_by | Syft cataloger that discovered the package |

#### Relationships

- A SyftPackage depends on another SyftPackage.

    ```
    (SyftPackage)-[:DEPENDS_ON]->(SyftPackage)
    ```

- A canonical Package (ontology) is detected as a SyftPackage.

    ```
    (Package)-[:DETECTED_AS]->(SyftPackage)
    ```

### Direct vs Transitive Dependencies

Direct and transitive dependencies are determined by graph structure rather than stored properties:

- **Direct dependencies**: Packages with no incoming `DEPENDS_ON` edges (nothing depends on them)
- **Transitive dependencies**: Packages that have incoming `DEPENDS_ON` edges

Query to find direct dependencies:

```cypher
MATCH (p:SyftPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```

Query to find transitive dependencies:

```cypher
MATCH (p:SyftPackage)
WHERE exists((p)<-[:DEPENDS_ON]-())
RETURN p.name
```
