# Debian Security Tracker Queries

## How Debian rates one CVE in each release

```cypher
MATCH (e:DebianSecurityTrackerEntry {cve_id: 'CVE-2005-2541'})
RETURN e.release, e.release_version, e.source_package, e.status, e.urgency,
       e.fixed_version, e.not_affected
ORDER BY e.release
```
