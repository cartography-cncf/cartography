# Syft Configuration

## Prerequisites

Install [Syft](https://github.com/anchore/syft) to generate software bill of
materials reports.

## Configure Cartography

Set `--syft-source` to a local path, `s3://bucket/prefix`,
`gs://bucket/prefix`, or `azblob://account/container/prefix`.

## Run Cartography

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --selected-modules syft \
            --syft-source /path/to/syft/results
```

For reports stored in S3:

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --selected-modules syft \
            --syft-source s3://my-security-bucket/scans/syft/
```

## Input Artifacts

### Generate Input Artifacts

Generate reports in Syft's native JSON format, not CycloneDX:

```bash
syft <image> -o syft-json=output.json
```

### Input Format

Required fields in the JSON are:

- `artifacts`: List of package objects with `id`, `name`, and `version`.
- `artifactRelationships`: List of dependency relationships. This field is
  optional but recommended.

## Advanced Configuration

Deprecated local and S3 report-source flags remain accepted until Cartography
v1.0.0 and emit warnings when used. New configurations should use
`--syft-source`.
