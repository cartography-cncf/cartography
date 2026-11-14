# CVE Metadata Configuration

## Authentication

An NVD API key is optional. When provided, Cartography fetches current CVE
metadata from the NVD API v2.0. Store the key in an environment variable and
pass its name with `--cve-metadata-nist-api-key-env-var`.

Without an API key, Cartography downloads the NVD yearly JSON feeds.

The EPSS API, the CISA KEV catalog, and CISA Vulnrichment need no credentials.

## Configure Cartography

No explicit enable flag is required. Include `cve_metadata` in the selected
module list or run all modules.

Use `--cve-metadata-src` multiple times to select metadata sources. Valid
values are `nvd`, `epss`, `kev`, and `vulnrichment`. All sources are enabled by
default. Each one downloads:

| Source | Download per sync |
| --- | --- |
| `nvd` | One request per 100 CVEs with an API key, otherwise one yearly feed per CVE year |
| `epss` | One request per 100 CVEs |
| `kev` | The KEV catalog JSON, about 2 MB |
| `vulnrichment` | The Vulnrichment repository tarball, about 100 MB |

Nothing is downloaded when the graph has no `CVE` nodes.

## Run Cartography

Enrich CVEs with all sources:

```bash
cartography \
  --selected-modules cve_metadata \
  --cve-metadata-src nvd \
  --cve-metadata-src epss \
  --cve-metadata-src kev \
  --cve-metadata-src vulnrichment
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
- [CISA Known Exploited Vulnerabilities catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [CISA Vulnrichment](https://github.com/cisagov/vulnrichment)
- [SSVC](https://certcc.github.io/SSVC/)
