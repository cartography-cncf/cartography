# Syft Configuration

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--syft-results-dir` | Path to directory containing Syft JSON results |
| `--syft-s3-bucket` | S3 bucket containing Syft scan results |
| `--syft-s3-prefix` | S3 prefix path containing Syft scan results |

## Examples

### Local Files

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --syft-results-dir /path/to/syft/results
```

### S3 Storage

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --syft-s3-bucket my-security-bucket \
            --syft-s3-prefix scans/syft/
```

## File Format

Syft JSON files should be in Syft's native JSON format (not CycloneDX):

```bash
syft <image> -o syft-json=output.json
```

Required fields in the JSON:
- `artifacts`: List of package objects with `id`, `name`, `version`
- `artifactRelationships`: List of dependency relationships (optional but recommended)
