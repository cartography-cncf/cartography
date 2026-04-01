## CVE Metadata Configuration

This module enriches existing CVE nodes in the graph with metadata from external sources. Unlike the deprecated [CVE](../cve/) module which imports all CVEs from NIST, this module only fetches metadata for CVEs already present in the graph from other modules (e.g., CrowdStrike, Semgrep, SentinelOne).

### Data Sources

- **NVD** — CVSS scores, descriptions, references, weaknesses, and CISA KEV (Known Exploited Vulnerabilities) data from the [NVD JSON feeds](https://nvd.nist.gov/vuln/data-feeds).
- **EPSS** — Exploit Prediction Scoring System scores from [FIRST.org](https://www.first.org/epss/).

### Usage

No explicit enable flag is needed. Include `cve_metadata` in your module list or run all modules.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--cve-metadata-src` | List of metadata sources to enable. Can be specified multiple times. Valid values: `nvd`, `epss`. | All sources enabled |

### Examples

Enrich CVEs with all sources:

```bash
cartography --cve-metadata-src nvd --cve-metadata-src epss
```

Enrich CVEs with only EPSS scores:

```bash
cartography --cve-metadata-src epss
```
