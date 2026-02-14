# Syft Module

The Syft module creates `SyftPackage` nodes with `DEPENDS_ON` dependency relationships from [Syft](https://github.com/anchore/syft), and enriches existing `TrivyPackage` nodes with dependency graph information.

## Purpose

While Trivy provides vulnerability scanning and creates `TrivyPackage` nodes with CVE findings, it lacks dependency relationship information. Syft complements Trivy by:

1. Creating `SyftPackage` nodes with `DEPENDS_ON` relationships between them
2. Creating `DEPENDS_ON` MatchLinks between existing `TrivyPackage` nodes for CVE tracing

This enables powerful queries like tracing CVEs through the dependency tree to find which direct dependencies need updating.

## Usage

Run Syft **after** Trivy in your cartography sync. Syft creates its own package nodes and also enriches existing TrivyPackage nodes.

### Generate Syft Output

```bash
# Generate Syft JSON for an image
syft nginx:latest -o syft-json=nginx-syft.json
```

### Run Cartography

```bash
# With local files
cartography --trivy-results-dir ./results --syft-results-dir ./results

# With S3
cartography --trivy-s3-bucket my-bucket --trivy-s3-prefix trivy/ \
            --syft-s3-bucket my-bucket --syft-s3-prefix syft/
```

## Key Queries

### Browse the SyftPackage dependency tree

```cypher
MATCH path = (p:SyftPackage)-[:DEPENDS_ON*1..5]->(dep:SyftPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN path
```

### Find CVEs in transitive dependencies and trace to direct deps

Uses TrivyPackage DEPENDS_ON MatchLinks for CVE tracing. Direct vs transitive is determined by graph structure:
- **Direct deps**: packages with no incoming DEPENDS_ON edges (nothing depends on them)
- **Transitive deps**: packages that have incoming DEPENDS_ON edges

```cypher
MATCH (cve:TrivyImageFinding)-[:AFFECTS]->(vuln:TrivyPackage)
WHERE exists((vuln)<-[:DEPENDS_ON]-())
MATCH (direct:TrivyPackage)-[:DEPENDS_ON*1..5]->(vuln)
WHERE NOT exists((direct)<-[:DEPENDS_ON]-())
RETURN cve.cve_id, vuln.name AS vulnerable_package, direct.name AS update_this
```

### Find all SyftPackages that depend on a specific package

```cypher
MATCH (upstream:SyftPackage)-[:DEPENDS_ON*1..10]->(dep:SyftPackage {name: 'lodash'})
RETURN DISTINCT upstream.name
```

## Schema

See [schema.md](schema.md) for details on created relationships.
