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
cd /path/to/your/repository
zizmor --format=json-v1 --no-exit-codes --no-ignores . > zizmor-report.json
```

Use `json-v1` rather than `json`. The unversioned alias tracks whatever the
current format version is, so a future zizmor release would silently change the
shape of the report. `--no-exit-codes` suppresses the exit codes zizmor returns
when findings are present, which otherwise fail the CI step that generates the
report.

Run zizmor **from the repository root, with a relative path**. Nothing in a
report says where the repository root is, so a finding reported under an
absolute path cannot be turned into the repository-relative path that
`GitHubWorkflow.path` stores. Such findings are skipped with a warning, and
because a skipped finding is still an open one, cleanup for that repository is
withheld for the run.

`--no-ignores` is what makes suppressed findings appear at all. Without it,
zizmor omits a finding suppressed by a `# zizmor: ignore[...]` comment entirely,
so it never reaches the graph and the `ignored` property is never true. With it,
the finding is reported and marked `ignored`. Drop the flag if you would rather
suppressed findings simply not be ingested; the trade-off is that you lose the
ability to audit what has been suppressed.

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

A repository may only appear once, and every report listed under it must
describe the **same branch**, the one named by `branch`. Two entries for one
repository are rejected, and comparison ignores case because GitHub repository
names are unique without regard to it.

That branch should be the repository's default branch. Findings attach to
`GitHubWorkflow` and `GitHubAction` nodes, which the GitHub module builds from
the default branch only: it lists workflows through the Actions API and reads
their YAML at `HEAD`. A finding from another branch would attach to the default
branch's workflow node, asserting something false, and an action used only on
that other branch has no node to attach to at all.

Nothing enforces this, because a report does not say which branch it came from.
Mixing branches under one entry is not rejected, it is simply wrong: `branch` is
not part of a finding's id, so the same finding on two branches collides on one
node and whichever report loads last wins.

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
