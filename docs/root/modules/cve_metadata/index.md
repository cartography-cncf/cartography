# CVE Metadata

The CVE Metadata module enriches existing `CVE` nodes with metadata from:

- NVD: CVSS scores, descriptions, references, weaknesses, and the copy of CISA
  Known Exploited Vulnerabilities data that NVD embeds in its records.
- EPSS: Exploit Prediction Scoring System scores from FIRST.
- CISA KEV: the Known Exploited Vulnerabilities catalog itself, including the
  ransomware use and forensic triage flags.
- CISA Vulnrichment: the SSVC decision points (Exploitation, Automatable,
  Technical Impact) that CISA adds to CVE records.
- ENISA EU Vulnerability Database (EUVD): the CVSS score, description,
  references, and publication date of CVEs that NVD has not scored.

Unlike the deprecated [CVE module](../cve/index.md), this module does not import every
CVE or create `CVE` nodes. Modules such as CrowdStrike, Semgrep, SentinelOne,
and Trivy must create those nodes first.

When all modules run together, the sync order places `cve_metadata` after
CVE-producing modules. When run alone, it enriches nodes from previous syncs
and skips processing if no `CVE` nodes exist.

## Known exploited vulnerabilities

`CVEMetadata.is_kev` comes from the KEV catalog when the `kev` source is
enabled and the catalog was fetched, so a CVE the catalog does not list is
`false` even if NVD's copy still lists it. When the catalog is not available,
`is_kev` falls back to NVD's copy. `is_kev_source` records which one was used.

## SSVC decisions

The SSVC fields hold the decision in CISA's Vulnrichment ADP container. They
are unset when Vulnrichment has no decision for the CVE;
`vulnrichment_updated_at` is set whenever Vulnrichment has a record for it.

CISA publishes Vulnrichment only as a git repository with one JSON file per
CVE, about 200,000 files. Rather than request each CVE, Cartography streams the
repository's gzipped tarball once per sync and parses only the files of CVEs
already in the graph. The archive is never held in memory or written to disk.

## CVEs that NVD has not scored

NVD can take weeks to score a new CVE, and some it never scores. For each CVE
without an NVD CVSS score that NVD has not rejected, the sync looks the CVE up
in EUVD and fills the CVSS fields from EUVD's score. It also fills the
description, references, and publication date where NVD has none. EUVD never
replaces a value that NVD provides. `cvss_source` records whether the CVSS
fields came from `nvd` or `euvd`. `euvd_id` holds the EUVD identifier of each
CVE looked up there for which EUVD has a record listing the CVE as an alias.

EUVD has no bulk download, so the sync makes one request per CVE it looks up.
When the `nvd` source is disabled, no CVE has an NVD score, so every CVE is
looked up.

## Failed fetches

If the KEV catalog or the Vulnrichment archive cannot be fetched or read in
full, or holds no records, the sync continues without that source: `is_kev`
falls back to NVD's copy of the KEV data, and the SSVC fields are left unset.
A KEV catalog whose `count` disagrees with the number of entries it lists is
treated the same way.
If an EUVD request fails or EUVD answers in an unexpected shape, the sync stops
querying EUVD for the rest of the run and leaves the CVSS fields of unscored
CVEs unset.
The `CVEMetadataFeed` node records the KEV catalog version as
`kev_catalog_version` and the archive's commit as `vulnrichment_commit`. Each
is unset when its source was not used.

See [configuration](config.md) to select sources, [queries](queries.md) for
example queries, and the generated [schema](schema.md) for fields.

```{toctree}
config
schema
queries
```
