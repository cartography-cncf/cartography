# CVE Metadata

The CVE Metadata module enriches existing `CVE` nodes with metadata from:

- NVD: CVSS scores, descriptions, references, weaknesses, and CISA Known
  Exploited Vulnerabilities data.
- EPSS: Exploit Prediction Scoring System scores from FIRST.

Unlike the deprecated [CVE module](../cve/), this module does not import every
CVE or create `CVE` nodes. Modules such as CrowdStrike, Semgrep, SentinelOne,
and Trivy must create those nodes first.

When all modules run together, the sync order places `cve_metadata` after
CVE-producing modules. When run alone, it enriches nodes from previous syncs
and skips processing if no `CVE` nodes exist.

```{toctree}
config
schema
```
