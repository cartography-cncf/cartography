## CVE Metadata Configuration

This module enriches existing CVE nodes in the graph with metadata from external sources. Unlike the deprecated [CVE](../cve/) module which imports all CVEs from NIST, this module only fetches metadata for CVEs already present in the graph from other modules (e.g., CrowdStrike, Semgrep, SentinelOne).

### Data Sources

- **NVD** — CVSS scores, descriptions, references, weaknesses, and CISA KEV (Known Exploited Vulnerabilities) data from the [NIST NVD API v2.0](https://nvd.nist.gov/developers/vulnerabilities) when an API key is provided, otherwise from the [NVD JSON feeds](https://nvd.nist.gov/vuln/data-feeds).
- **EPSS** — Exploit Prediction Scoring System scores from [FIRST.org](https://www.first.org/epss/).

### Usage

No explicit enable flag is needed. Include `cve_metadata` in your module list or run all modules.

### Enrichment order

`cve_metadata` only enriches `:CVE` nodes that are already present in the graph — it does not create them. Modules that produce `:CVE` nodes (e.g. CrowdStrike, Semgrep, SentinelOne, Trivy) must run **before** `cve_metadata` in the same sync. Running all modules in a single cartography invocation is sufficient: the module ordering in `cartography/sync.py` places `cve_metadata` after the CVE-producing modules, so the enrichment pass picks up every freshly ingested CVE.

If you only run `cve_metadata` in isolation, it will enrich the CVEs from the previous sync and skip the step silently if no `:CVE` nodes exist yet.

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--cve-metadata-src` | List of metadata sources to enable. Can be specified multiple times. Valid values: `nvd`, `epss`. | All sources enabled |
| `--cve-metadata-nist-api-key-env-var` | Environment variable name holding an NVD API v2.0 key. When set, CVEs are fetched one-by-one via the API (fresher data); otherwise the module downloads yearly JSON feeds. | None |

### Examples

Enrich CVEs with all sources:

```bash
cartography --cve-metadata-src nvd --cve-metadata-src epss
```

Enrich CVEs with only EPSS scores:

```bash
cartography --cve-metadata-src epss
```
