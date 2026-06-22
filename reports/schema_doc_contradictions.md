# Cartography schema documentation audit, 2026-06-22

Cartography model code is treated as the source of truth. Explicit docs arrow patterns are authoritative for docs-side source, relationship, and target labels.

## Summary

- Model nodes inspected: 615
- Model relationships inspected: 1539
- Docs node sections inspected: 658
- Findings emitted: 1537

| Severity | Count |
|---|---:|
| P2 | 1478 |
| P3 | 59 |

## Findings By Module

| Module | Severity | Count |
|---|---|---:|
| aws | P2 | 606 |
| gcp | P2 | 170 |
| azure | P2 | 117 |
| ontology | P2 | 88 |
| github | P2 | 63 |
| entra | P2 | 50 |
| semgrep | P2 | 44 |
| gitlab | P2 | 41 |
| kubernetes | P2 | 39 |
| microsoft | P2 | 37 |
| gsuite | P2 | 36 |
| okta | P2 | 36 |
| aws | P3 | 18 |
| pagerduty | P3 | 17 |
| slack | P2 | 16 |
| googleworkspace | P2 | 13 |
| pagerduty | P2 | 12 |
| gitlab | P3 | 10 |
| keycloak | P2 | 10 |
| spacelift | P2 | 10 |
| trivy | P2 | 10 |
| oci | P2 | 9 |
| vercel | P2 | 9 |
| gcp | P3 | 8 |
| cve | P2 | 7 |
| duo | P2 | 7 |
| jamf | P2 | 6 |
| snipeit | P2 | 5 |
| bigfix | P2 | 4 |
| crowdstrike | P2 | 4 |
| digitalocean | P2 | 4 |
| github | P3 | 4 |
| openai | P2 | 4 |
| scaleway | P2 | 4 |
| kandji | P2 | 3 |
| lastpass | P2 | 2 |
| ontology | P3 | 2 |
| sentinelone | P2 | 2 |
| socketdev | P2 | 2 |
| workos | P2 | 2 |
| _cartography-metadata | P2 | 1 |
| aibom | P2 | 1 |
| cloudflare | P2 | 1 |
| docker_scout | P2 | 1 |
| syft | P2 | 1 |
| tailscale | P2 | 1 |

## P1 Contradictions

No P1 contradictions were detected.

## P2 And P3 Inventory

The JSON report contains every finding with the full required field set. This markdown report keeps non-P1 output summarized to avoid hiding hard contradictions in coverage noise.

| Severity | Issue Type | Count |
|---|---|---:|
| P2 | missing_docs_property | 679 |
| P2 | missing_docs_relationship | 253 |
| P2 | docs_only_relationship | 237 |
| P2 | docs_only_property | 225 |
| P2 | doc_only_node_section | 59 |
| P3 | unlabeled_relationship_pattern | 31 |
| P3 | ambiguous_relationship_pattern | 28 |
| P2 | missing_docs_node_section | 25 |

Recommended next: decide which P2 coverage gaps are useful enough to document; no P1 docs contradictions remain.
