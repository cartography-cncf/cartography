<!-- Generated from the data model. Do not edit manually. -->

## Zizmor Schema

```mermaid
graph LR
```

### ZizmorFinding

A CI supply-chain weakness reported by zizmor against a GitHub Actions file.

Zizmor reports are ingested from files rather than by running the binary, so
there is no tenant-like node to scope cleanup to. Stale findings are instead
removed per repository by the module's cleanup function.

> **Ontology Mapping**: This node uses the ontology label [`SecurityIssue`](#ontology-securityissue).

#### Properties

| Field | Index | Description |
|-------|-------|-------------|
| id | Yes | Synthetic finding identifier. Zizmor does not emit a stable finding ID, so this is a hash of the audit, repository, workflow path, and YAML route. |
| firstseen |  | Timestamp when a sync job first created this node. |
| lastupdated | Yes | Timestamp of the last sync that observed this node. |
| annotation |  | Zizmor's explanation of why the primary location is a problem. |
| audit_id | Yes | Identifier of the zizmor audit that produced the finding, such as `template-injection` or `unpinned-uses`. |
| branch |  | Repository branch the scanned workflow files were read from. |
| confidence |  | Confidence determined by zizmor: `low`, `medium`, or `high`. |
| description |  | Short description of the weakness reported by the audit. |
| end_col |  | One-based column where the primary location ends. |
| end_line |  | One-based line where the primary location ends. |
| file_path | Yes | Repository-relative path of the audited workflow or action file. |
| fix_dispositions |  | Disposition of each available fix, `safe` or `unsafe`, in the same order as `fix_titles`. |
| fix_titles |  | Titles of the fixes zizmor can apply for this finding. |
| ignored |  | Whether the finding was suppressed by a `# zizmor: ignore[...]` comment. Only true when the report was produced with `--no-ignores`, since zizmor otherwise omits suppressed findings entirely. Rules disabled through zizmor's configuration file are reported like any other finding. |
| persona |  | Persona the finding is reported for: `regular`, `pedantic`, or `auditor`. |
| repository | Yes | Repository the finding was discovered in, in `owner/repo` form. |
| repository_url | Yes | Full URL of the repository the finding was discovered in. |
| severity | Yes | Severity determined by zizmor: `informational`, `low`, `medium`, or `high`. |
| snippet |  | Source excerpt of the primary location. |
| start_col |  | One-based column where the primary location starts. |
| start_line |  | One-based line where the primary location starts. |
| url |  | Link to the zizmor documentation page for this audit. |
| uses_reference | Yes | Raw `uses` reference the finding points at, when the finding concerns a step or job that calls an action. Null for other findings. |
| yaml_route |  | Dotted YAML path of the offending node, such as `jobs.greet.steps.0.run`. |

#### Relationships

- `(:ZizmorFinding)-[:AFFECTS]->(:GitHubAction)`: Links a zizmor finding to the action it concerns.

Only findings whose location is a `uses` key resolve to an action, so this
relationship is absent for findings reported against a `run` block, a job's
permissions, or a workflow trigger.

- `(:ZizmorFinding)-[:AFFECTS]->(:GitHubWorkflow)`: Links a zizmor finding to the GitHub Actions workflow it was found in.

- `(:ZizmorFinding)-[:FOUND_IN]->(:GitHubRepository)`: Links a zizmor finding to the GitHub repository containing the audited file.
