# Wiz

```{toctree}
config
schema
```

Cartography can ingest Wiz issues, vulnerability findings, detection findings,
and failing configuration findings from the Wiz GraphQL API.

Wiz issues are labeled as `SecurityIssue`. All Wiz findings are labeled as
`Risk`; CVE-backed vulnerability findings are also labeled as `CVE`, while
configuration, detection, and non-CVE vulnerability findings are labeled as
`SecurityIssue`.
