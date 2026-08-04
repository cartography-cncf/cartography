# Semgrep Configuration

Semgrep supports both Semgrep Cloud API ingestion and Semgrep OSS report ingestion.

## Prerequisites

To link findings to repositories, ingest the corresponding GitHub or GitLab module before running Semgrep.

## Authentication

For Semgrep Cloud, create a token by following the [SEMGREP_APP_TOKEN guide](https://semgrep.dev/docs/semgrep-ci/running-semgrep-ci-with-semgrep-cloud-platform/#creating-a-semgrep_app_token). Store the token in an environment variable.

Semgrep OSS report ingestion does not require Semgrep API credentials.

## Required Permissions

The Semgrep Cloud token requires the **Agent (CI)** and **Web API** scopes.

## Configure Cartography

### Semgrep Cloud

Use `--semgrep-app-token-env-var` to provide the name of the environment variable containing the token.

### Semgrep OSS

Use `--semgrep-oss-source` to provide the path to a repository mapping YAML file.

## Run Cartography

### Semgrep Cloud

```bash
export SEMGREP_APP_TOKEN='<app-token>'
cartography \
  --selected-modules semgrep \
  --semgrep-app-token-env-var SEMGREP_APP_TOKEN
```

### Semgrep OSS

```bash
cartography \
  --selected-modules semgrep \
  --semgrep-oss-source /path/to/repository_mappings.yaml
```

## Input Artifacts

### Input Format

The repository mapping file must:

- Be valid UTF-8 YAML.
- Contain a top-level `repositories` list.
- Give each repository entry `provider`, `owner`, `repo`, `url`, `branch`, and a nonempty `reports` list.
- Set `provider` to `github` or `gitlab`.
- Point each `reports` entry to exactly one Semgrep OSS JSON artifact for its repository.

For sharded or monorepo scans, list each JSON artifact separately. A `reports` entry cannot be a directory or object storage prefix containing multiple files.

```yaml
repositories:
  - provider: "github"
    owner: "simpsoncorp"
    repo: "sample_repo"
    url: "https://github.com/simpsoncorp/sample_repo"
    branch: "main"
    reports:
      - "/path/to/sample_repo-semgrep.json"
  - provider: "github"
    owner: "different-org"
    repo: "different-repo"
    url: "https://github.com/different-org/different-repo"
    branch: "main"
    reports:
      - "s3://security-artifacts/semgrep/different-repo/report-1.json"
      - "s3://security-artifacts/semgrep/different-repo/report-2.json"
  - provider: "gitlab"
    owner: "simpsoncorp"
    repo: "gitlab_repo"
    url: "https://gitlab.com/simpsoncorp/gitlab_repo"
    branch: "main"
    reports:
      - "/path/to/gitlab_repo-semgrep.json"
```

## Advanced Configuration

To ingest Semgrep dependencies, pass the desired language ecosystems as a comma-separated string, such as `gomod,npm`, to `--semgrep-dependency-ecosystems`. The supported ecosystems are defined in `cartography.intel.semgrep.dependencies`.
