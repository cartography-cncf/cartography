# Semgrep

Cartography ingests Semgrep Cloud findings, dependency inventory, Assistant data,
and Semgrep OSS SAST report artifacts. The module links findings and dependencies
to existing GitHub repositories or GitLab projects when matching repository nodes
are available.

Cloud ingestion supports SAST, Supply Chain (SCA), and Secrets findings. OSS
ingestion supports SAST findings from explicit JSON reports and requires a
repository mapping file because Semgrep OSS reports do not contain repository
identity. See [Configuration](config.md) for authentication, report mapping, and
repository matching requirements.

## Finding analysis

Semgrep Cloud SAST findings receive a `risk_severity` property from
post-ingestion analysis. Findings in archived GitHub repositories are assigned
`INFO`; otherwise, the value follows the finding severity.

Semgrep SCA findings receive a `reachability_risk` property based on severity,
reachability, and the reachability check. Findings in archived repositories or
findings confirmed as unreachable are assigned `INFO`. Other combinations use
the risk levels defined by `SEMGREP_SCA_RISK_ANALYSIS`, based on the likelihood
and impact approach from NIST SP 800-30 Revision 1 and Semgrep reachability
exposure guidance.

Cloud-only SAST data includes `line_of_code_url`, `state`, `fix_status`,
`triage_status`, `opened_at`, `risk_severity`, and Semgrep Assistant
relationships.

```{toctree}
config
schema
```
