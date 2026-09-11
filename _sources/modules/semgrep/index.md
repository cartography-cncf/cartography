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

Each Semgrep OSS repository entry represents the intended snapshot for that
repository in the current run. After all listed reports are processed
successfully, Cartography removes stale OSS findings scoped to that repository
URL. If any report cannot be resolved or parsed, or does not have the expected
Semgrep shape, Cartography skips cleanup for that repository to avoid deleting
findings from an incomplete snapshot.

For OSS findings, `FOUND_IN` relationships require an existing
`GitHubRepository` or `GitLabProject`. GitHub repositories match the mapping
file's `url` to node `id`; GitLab projects match it to `web_url`.

Cloud-only SAST data includes `line_of_code_url`, `state`, `fix_status`,
`triage_status`, `opened_at`, `risk_severity`, and Semgrep Assistant
relationships.

```{toctree}
config
schema
analysis
```
