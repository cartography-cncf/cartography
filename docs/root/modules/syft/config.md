# Syft Configuration

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--syft-source` | Syft report source. Accepts a local path, `s3://bucket/prefix`, `gs://bucket/prefix`, or `azblob://account/container/prefix`. |

Deprecated local and S3 report-source flags remain accepted until Cartography v1.0.0 and emit warnings when used. New configurations should use `--syft-source`.

## Examples

### Local Files

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --syft-source /path/to/syft/results
```

### S3 Storage

```bash
cartography --neo4j-uri bolt://localhost:7687 \
            --syft-source s3://my-security-bucket/scans/syft/
```

## File Format

Syft JSON files should be in Syft's native JSON format (not CycloneDX):

```bash
syft <image> -o syft-json=output.json
```

Required fields in the JSON:
- `artifacts`: List of package objects with `id`, `name`, `version`
- `artifactRelationships`: List of dependency relationships (optional but recommended)
