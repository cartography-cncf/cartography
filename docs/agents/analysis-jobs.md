# Adding Analysis Jobs to Cartography Modules

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Troubleshooting](troubleshooting.md)

Analysis jobs are post-ingestion queries that enrich the graph with computed relationships and properties. They run after data is loaded and perform cross-node analysis that cannot be done during the initial load phase.

## Table of Contents

1. [Overview](#overview) - What are analysis jobs and when to use them
2. [Types of Analysis Jobs](#types-of-analysis-jobs) - Global vs scoped analysis
3. [Creating an Analysis Job](#creating-an-analysis-job) - JSON format and query structure
4. [Calling Analysis Jobs](#calling-analysis-jobs) - Integration with your module
5. [Reference Examples](#reference-examples) - Patterns from GCP and AWS modules
6. [Audit Status](#audit-status) - Current state of analysis jobs in the codebase

## Overview

Analysis jobs perform graph enrichment after data ingestion. Common use cases include:

- **Internet exposure analysis**: Determining if resources are exposed to the internet based on security group rules, load balancers, and network configurations
- **Permission inheritance**: Computing transitive permissions through role hierarchies
- **Cross-resource linking**: Connecting nodes from different data sources (e.g., linking Human nodes to GSuiteUser nodes)
- **Risk scoring**: Computing risk scores based on multiple factors

### When to Use Analysis Jobs

Use analysis jobs when you need to:
1. Compute properties that depend on multiple nodes/relationships
2. Create relationships that span across different resource types
3. Perform transitive closure computations (e.g., inherited permissions)
4. Enrich data after all resources of a type have been loaded

### When NOT to Use Analysis Jobs

Don't use analysis jobs for:
1. Simple node-to-node relationships (use the data model instead)
2. Properties that can be computed during transform phase
3. Relationships that are already present in the source data

## Types of Analysis Jobs

### Global Analysis Jobs

Global analysis jobs run once after all accounts/projects are synced. They operate on the entire graph.

**Location**: `cartography/data/jobs/analysis/`

**Called with**: `run_analysis_job()` or `run_analysis_and_ensure_deps()`

**Example**: Internet exposure analysis that needs to see all security groups across all accounts.

### Scoped Analysis Jobs

Scoped analysis jobs run once per account/project/tenant. They operate on a subset of the graph.

**Location**: `cartography/data/jobs/scoped_analysis/`

**Called with**: `run_scoped_analysis_job()`

**Example**: IAM instance profile analysis that runs per AWS account.

## Creating an Analysis Job

Analysis jobs are JSON files with an array of Cypher statements.

### JSON Format

```json
{
  "name": "Human-readable name for logging",
  "statements": [
    {
      "__comment__": "Optional comment explaining this query",
      "query": "MATCH (n:NodeType) WHERE ... SET n.property = value",
      "iterative": false
    },
    {
      "__comment__": "Iterative queries for large datasets",
      "query": "MATCH (n:NodeType) WHERE n.property IS NULL WITH n LIMIT $LIMIT_SIZE SET n.property = value RETURN COUNT(*) AS TotalCompleted",
      "iterative": true,
      "iterationsize": 1000
    }
  ]
}
```

### Query Structure

**Non-iterative queries**: Run once, best for queries that touch a manageable number of nodes.

```json
{
  "query": "MATCH (instance:GCPInstance) WHERE ... SET instance.exposed_internet = true",
  "iterative": false
}
```

**Iterative queries**: Run in batches, required for large datasets. Must return `TotalCompleted` count.

```json
{
  "query": "MATCH (n:Node) WHERE n.stale = true WITH n LIMIT $LIMIT_SIZE DELETE n RETURN COUNT(*) AS TotalCompleted",
  "iterative": true,
  "iterationsize": 1000
}
```

### Available Parameters

Analysis jobs receive `common_job_parameters` which typically includes:
- `$UPDATE_TAG`: The current sync timestamp
- `$LIMIT_SIZE`: Batch size for iterative queries (set automatically)
- Module-specific parameters (e.g., `$AWS_ID`, `$PROJECT_ID`)

## Calling Analysis Jobs

### In Module `__init__.py`

The main module entry point should call analysis jobs after all data is synced.

#### Pattern 1: Global Analysis (after all accounts/projects)

```python
from cartography.util import run_analysis_job

@timeit
def start_your_module_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
    }

    # Sync all accounts/projects
    for account in accounts:
        _sync_one_account(neo4j_session, account, config.update_tag, common_job_parameters)

    # Run global analysis jobs AFTER all accounts are synced
    run_analysis_job(
        "your_module_exposure_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
```

#### Pattern 2: Scoped Analysis (per account/project)

```python
from cartography.util import run_scoped_analysis_job

def _sync_one_account(
    neo4j_session: neo4j.Session,
    account_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    common_job_parameters["ACCOUNT_ID"] = account_id

    # Sync resources for this account
    sync_resources(neo4j_session, account_id, update_tag, common_job_parameters)

    # Run scoped analysis for this account
    run_scoped_analysis_job(
        "your_module_account_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
```

#### Pattern 3: Conditional Analysis (with dependency checking)

```python
from cartography.util import run_analysis_and_ensure_deps

def _perform_analysis(
    requested_syncs: List[str],
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    # Only run if required modules were synced
    run_analysis_and_ensure_deps(
        "your_module_combined_analysis.json",
        {"ec2:instance", "ec2:security_group"},  # Required sync modules
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )
```

## Reference Examples

### GCP Module Pattern

The GCP module runs analysis jobs at the end of `start_gcp_ingestion()`:

```python
# From cartography/intel/gcp/__init__.py

def start_gcp_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    # ... sync all orgs, folders, projects, and resources ...

    # Run analysis jobs after ALL projects are synced
    run_analysis_job(
        "gcp_compute_asset_inet_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_gke_asset_exposure.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_gke_basic_auth.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "gcp_compute_instance_vpc_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
```

### AWS Module Pattern

The AWS module uses both scoped (per-account) and global analysis:

```python
# From cartography/intel/aws/__init__.py

def _sync_one_account(...) -> None:
    # ... sync resources ...

    # Scoped analysis runs per-account
    run_scoped_analysis_job(
        "aws_ec2_iaminstanceprofile.json",
        neo4j_session,
        common_job_parameters,
    )

    run_analysis_job(
        "aws_lambda_ecr.json",
        neo4j_session,
        common_job_parameters,
    )


def _perform_aws_analysis(
    requested_syncs: List[str],
    neo4j_session: neo4j.Session,
    common_job_parameters: Dict[str, Any],
) -> None:
    # Global analysis with dependency checking
    run_analysis_and_ensure_deps(
        "aws_ec2_asset_exposure.json",
        {"ec2:instance", "ec2:security_group", "ec2:load_balancer", "ec2:load_balancer_v2"},
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )

    run_analysis_and_ensure_deps(
        "aws_eks_asset_exposure.json",
        {"eks"},
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )
```

### Semgrep Module Pattern

The Semgrep module calls a scoped analysis job within its findings sync:

```python
# From cartography/intel/semgrep/findings.py

def sync_findings(...) -> None:
    # ... load findings ...

    run_scoped_analysis_job(
        "semgrep_sca_risk_analysis.json",
        neo4j_session,
        common_job_parameters,
    )

    cleanup(neo4j_session, common_job_parameters)
```

## Audit Status

### Modules with Proper Analysis Job Integration

| Module | Analysis Jobs | Location |
|--------|--------------|----------|
| AWS | `aws_ec2_asset_exposure.json`, `aws_ec2_keypair_analysis.json`, `aws_eks_asset_exposure.json`, `aws_foreign_accounts.json`, `aws_lambda_ecr.json`, `aws_ecs_asset_exposure.json` | Global (in `_perform_aws_analysis`) |
| AWS | `aws_ec2_iaminstanceprofile.json` | Scoped (per-account in `_sync_one_account`) |
| AWS S3 | `aws_s3acl_analysis.json` | Scoped (in `s3.py`) |
| GCP | `gcp_compute_asset_inet_exposure.json`, `gcp_gke_asset_exposure.json`, `gcp_gke_basic_auth.json`, `gcp_compute_instance_vpc_analysis.json` | Global (end of `start_gcp_ingestion`) |
| GSuite | `gsuite_human_link.json` | Global (end of `start_gsuite_ingestion`) |
| Keycloak | `keycloak_inheritance.json` | Global (end of `start_keycloak_ingestion`) |
| Semgrep | `semgrep_sca_risk_analysis.json` | Scoped (in `findings.py`) |

> **Note**: `aws_ecs_asset_exposure.json` is marked as deprecated in favor of the ontology `LoadBalancer-[:EXPOSE]->Container` pattern, but is still called for backward compatibility.

## Best Practices

1. **Call analysis jobs at the right scope**: Global jobs after all accounts, scoped jobs per-account
2. **Use dependency checking**: For jobs that require specific modules to have run first
3. **Document your analysis jobs**: Explain what each query does with `__comment__`
4. **Test analysis jobs**: Write integration tests that verify the analysis produces expected results
5. **Consider performance**: Use iterative queries for large datasets
6. **Clean up stale data**: Analysis jobs that create relationships should also clean up old ones
