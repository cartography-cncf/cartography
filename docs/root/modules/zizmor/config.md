# Zizmor Configuration

## Prerequisites

Run the GitHub module before Zizmor. Findings attach to `GitHubRepository`,
`GitHubWorkflow`, and `GitHubAction` nodes, so those must already exist for the
relationships to be created. In the default sync order, Zizmor runs after
GitHub automatically.

Workflow and action relationships additionally require the GitHub module to
have parsed workflow YAML, which is what populates `GitHubWorkflow.path` and
the `GitHubAction` nodes.

## Configure Cartography

Set `--zizmor-source` to the repository mapping file described below. It
accepts a local file path or a supported object storage URI (`s3://`, `gs://`,
`azblob://`).

## Run Cartography

Run with a local mapping file:

```bash
cartography --selected-modules zizmor --zizmor-source /path/to/zizmor-mapping.yaml
```

Run with a mapping file in object storage:

```bash
cartography --selected-modules zizmor --zizmor-source s3://my-bucket/zizmor/mapping.yaml
```

## Input Artifacts

Cartography ingests pre-generated zizmor JSON reports. It does not run the
zizmor binary.

### Generate Input Artifacts

Produce reports with the versioned JSON format:

```bash
zizmor --format=json-v1 --no-exit-codes . > zizmor-report.json
```

Use `json-v1` rather than `json`. The unversioned alias tracks whatever the
current format version is, so a future zizmor release would silently change the
shape of the report. `--no-exit-codes` suppresses the exit codes zizmor returns
when findings are present, which otherwise fail the CI step that generates the
report.

Findings are only ingested for personas that zizmor was asked to report. Pass
`--persona=pedantic` or `--persona=auditor` if you want the lower-signal audits
in the graph as well.

### Input Format

The `--zizmor-source` locator must resolve to exactly one YAML file. Zizmor's
JSON output carries no repository identity: for a local run, the only path
information is the literal argument passed on the command line. The mapping
file supplies that identity and points at the reports for each repository.

```yaml
repositories:
  - owner: "simpsoncorp"
    repo: "sample_repo"
    url: "https://github.com/simpsoncorp/sample_repo"
    branch: "main"
    reports:
      - "s3://security-artifacts/zizmor/sample_repo/main.json"
  - owner: "simpsoncorp"
    repo: "other_repo"
    url: "https://github.com/simpsoncorp/other_repo"
    branch: "main"
    reports:
      - "/var/lib/zizmor/other_repo.json"
```

| Field | Required | Description |
|-------|----------|-------------|
| `repositories` | Yes | Non-empty list of repository entries. |
| `owner` | Yes | GitHub organization or user that owns the repository. |
| `repo` | Yes | Repository name. |
| `url` | Yes | Repository URL. Must match `GitHubRepository.id`. |
| `branch` | Yes | Branch the scanned workflow files were read from. |
| `reports` | Yes | Non-empty list of report locators. Each must resolve to exactly one JSON artifact. |

A repository may only appear once. List all of its reports under that single
entry's `reports` rather than repeating the entry, including when they come from
different branches. Two entries for one repository are rejected, and comparison
ignores case because GitHub repository names are unique without regard to it.

`owner` and `repo` are used to rebuild the `GitHubAction` identifiers that the
GitHub module assigns, so they must match the values the GitHub module synced.

Each entry in `reports` is resolved independently and may use a different
scheme from the mapping file itself. A locator that resolves to zero artifacts,
to more than one artifact, to a non-JSON artifact, or to something that is not
a zizmor JSON v1 report is skipped with a warning, and cleanup for that
repository is skipped for the run.

Reports must describe a checked-out repository. Findings zizmor read from stdin
carry no path, so they cannot be joined to a workflow; they are skipped, and
because a skipped finding is still an open one, cleanup for that repository is
skipped as well.

## References

- [zizmor](https://github.com/zizmorcore/zizmor)
- [zizmor documentation](https://docs.zizmor.sh/)
- [zizmor audit reference](https://docs.zizmor.sh/audits/)
