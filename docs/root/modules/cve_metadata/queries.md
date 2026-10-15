# CVE Metadata Queries

## CVEs in the KEV catalog

```cypher
MATCH (m:CVEMetadata)
WHERE m.is_kev = true AND m.is_kev_source = 'kev'
RETURN m.id, m.kev_date_added, m.kev_due_date, m.kev_ransomware_use,
       m.kev_forensic_triage
ORDER BY m.kev_date_added DESC
```

## Automatable CVEs with total technical impact

```cypher
MATCH (m:CVEMetadata)-[:ENRICHES]->(c:CVE)
WHERE m.ssvc_automatable = 'yes' AND m.ssvc_technical_impact = 'total'
RETURN m.id, m.ssvc_exploitation, m.ssvc_timestamp, count(c) AS findings
```
