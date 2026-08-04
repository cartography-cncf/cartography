# CVE Metadata Configuration

## Authentication

An NVD API key is optional. When provided, Cartography fetches current CVE
metadata from the NVD API v2.0. Store the key in an environment variable and
pass its name with `--cve-metadata-nist-api-key-env-var`.

Without an API key, Cartography downloads the NVD yearly JSON feeds.

## Configure Cartography

No explicit enable flag is required. Include `cve_metadata` in the selected
module list or run all modules.

Use `--cve-metadata-src` multiple times to select metadata sources. Valid
values are `nvd` and `epss`. All sources are enabled by default.

## Run Cartography

Enrich CVEs with all sources:

```bash
cartography \
  --selected-modules cve_metadata \
  --cve-metadata-src nvd \
  --cve-metadata-src epss
```

Enrich CVEs with only EPSS scores:

```bash
cartography \
  --selected-modules cve_metadata \
  --cve-metadata-src epss
```

## References

- [NIST NVD API v2.0](https://nvd.nist.gov/developers/vulnerabilities)
- [NVD JSON feeds](https://nvd.nist.gov/vuln/data-feeds)
- [FIRST EPSS](https://www.first.org/epss/)
