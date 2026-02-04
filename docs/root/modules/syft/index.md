# Syft Module

The Syft module enriches TrivyPackage nodes with dependency graph information from [Syft](https://github.com/anchore/syft).

## Purpose

While Trivy provides vulnerability scanning and creates `TrivyPackage` nodes with CVE findings, it lacks dependency relationship information. Syft complements Trivy by creating `DEPENDS_ON` relationships between packages.

This enables powerful queries like tracing CVEs through the dependency tree to find which direct dependencies need updating.

## Usage

Run Syft **after** Trivy in your cartography sync. Syft enriches existing TrivyPackage nodes rather than creating new ones.

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

### Find CVEs in transitive dependencies and trace to direct deps

Direct vs transitive is determined by graph structure:
- **Direct deps**: packages with no incoming DEPENDS_ON edges (nothing depends on them)
- **Transitive deps**: packages that have incoming DEPENDS_ON edges

```cypher
MATCH (cve:TrivyImageFinding)-[:AFFECTS]->(vuln:TrivyPackage)
WHERE exists((vuln)<-[:DEPENDS_ON]-())
MATCH (direct:TrivyPackage)-[:DEPENDS_ON*1..5]->(vuln)
WHERE NOT exists((direct)<-[:DEPENDS_ON]-())
RETURN cve.cve_id, vuln.name AS vulnerable_package, direct.name AS update_this
```

### View dependency tree from direct dependencies

```cypher
MATCH path = (p:TrivyPackage)-[:DEPENDS_ON*1..5]->(dep:TrivyPackage)
WHERE NOT exists((p)<-[:DEPENDS_ON]-())
RETURN path
```

### Find all packages that depend on a vulnerable package

```cypher
MATCH (upstream:TrivyPackage)-[:DEPENDS_ON*1..10]->(vuln:TrivyPackage {name: 'lodash'})
RETURN DISTINCT upstream.name
```

## Schema

See [schema.md](schema.md) for details on created relationships.
