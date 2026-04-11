# Syft Module

The Syft module creates `SyftPackage` nodes with `DEPENDS_ON` dependency relationships from [Syft](https://github.com/anchore/syft).

## Purpose

While Trivy provides vulnerability scanning and creates `TrivyPackage` nodes with CVE findings, it lacks dependency relationship information. Syft complements Trivy by creating `SyftPackage` nodes with `DEPENDS_ON` relationships between them.

This enables powerful queries like browsing the dependency tree and identifying direct vs transitive dependencies.

## Usage

### Generate Syft Output

```bash
# Generate Syft JSON for an image
syft nginx:latest -o syft-json=nginx-syft.json
```

### Run Cartography

```bash
# With local files
cartography --syft-results-dir ./results

# With S3
cartography --syft-s3-bucket my-bucket --syft-s3-prefix syft/
```

## Key Queries

### Browse the SyftPackage dependency tree

```cypher
MATCH path = (p:SyftPackage)-[:DEPENDS_ON*1..5]->(dep:SyftPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN path
```

### Find all SyftPackages that depend on a specific package

```cypher
MATCH (upstream:SyftPackage)-[:DEPENDS_ON*1..10]->(dep:SyftPackage {name: 'lodash'})
RETURN DISTINCT upstream.name
```

## Schema

See [schema.md](schema.md) for details on created nodes and relationships.
