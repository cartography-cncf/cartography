# Syft Configuration

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--syft-source` | Syft report source. Accepts a local path, `s3://bucket/prefix`, `gs://bucket/prefix`, or `azblob://account/container/prefix`. |
| `--syft-results-dir` | Deprecated compatibility flag for a local Syft JSON results directory. Use `--syft-source` instead. |
| `--syft-s3-bucket` | Deprecated compatibility flag for an S3 bucket containing Syft scan results. Use `--syft-source s3://...` instead. |
| `--syft-s3-prefix` | Deprecated compatibility flag for an S3 prefix path. Use `--syft-source s3://...` instead. |

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
