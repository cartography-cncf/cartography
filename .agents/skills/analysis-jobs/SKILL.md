---
name: analysis-jobs
description: Add a post-ingestion analysis job (JSON Cypher file) to a Cartography module to enrich the graph after sync. Use when the user asks to compute internet exposure, propagate inherited permissions, link Human / canonical ontology nodes, score risk, or add cross-resource analysis after data is loaded.
---

# analysis-jobs

Analysis jobs are post-ingestion Cypher queries (JSON files) that enrich the graph with computed relationships and properties. They run **after** data is loaded and perform cross-node work that cannot be done during the initial load.

## When to use analysis jobs

Use them when you need to:

1. Compute properties that depend on multiple nodes / relationships.
2. Create relationships that span across resource types.
3. Perform transitive closure (e.g. inherited permissions).
4. Enrich data after all resources of a type are loaded.

**Do NOT** use analysis jobs for:

1. Simple node-to-node relationships (use the data model — see `add-relationship`).
2. Properties that can be computed during `transform()`.
3. Relationships already present in the source data.

## Critical rules

1. **Pick the right scope.** Global jobs run after all accounts/projects/tenants (`run_analysis_job`). Scoped jobs run once per account (`run_scoped_analysis_job`). Use dependency checking (`run_analysis_and_ensure_deps`) when a job needs specific upstream modules.
2. **Use iterative queries for large datasets.** They must return `COUNT(*) AS TotalCompleted`.
3. **Document each query** with `__comment__`.
4. **Clean up stale data** that the analysis job creates (don't leave orphan edges between syncs).

## Instructions

### Step 1 — Pick global vs scoped

| Type    | Runs                                  | Location                                    | Helper                          |
| ------- | ------------------------------------- | ------------------------------------------- | ------------------------------- |
| Global  | Once after all accounts / projects    | `cartography/data/jobs/analysis/`           | `run_analysis_job()`            |
| Scoped  | Once per account / project / tenant   | `cartography/data/jobs/scoped_analysis/`    | `run_scoped_analysis_job()`     |

Examples:

- Internet exposure that needs to see all security groups across all accounts -> **global**.
- IAM instance profile analysis that runs per AWS account -> **scoped**.

### Step 2 — Author the JSON file

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

### Step 3 — Write the queries

**Non-iterative** — single execution, OK for queries touching a manageable number of nodes:

```json
{
  "query": "MATCH (instance:GCPInstance) WHERE ... SET instance.exposed_internet = true",
  "iterative": false
}
```

**Iterative** — required for large datasets. Must return `TotalCompleted`:

```json
{
  "query": "MATCH (n:Node) WHERE n.stale = true WITH n LIMIT $LIMIT_SIZE DELETE n RETURN COUNT(*) AS TotalCompleted",
  "iterative": true,
  "iterationsize": 1000
}
```

### Step 4 — Available parameters

`common_job_parameters` is forwarded into the query. Typical params:

- `$UPDATE_TAG` — current sync timestamp.
- `$LIMIT_SIZE` — set automatically by the iterative runner.
- Module-specific (`$AWS_ID`, `$PROJECT_ID`, ...).

### Step 5 — Wire the call into your module

#### Pattern A — global analysis at end of ingestion

```python
from cartography.util import run_analysis_job

@timeit
def start_your_module_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    for account in accounts:
        _sync_one_account(neo4j_session, account, config.update_tag, common_job_parameters)

    run_analysis_job(
        "your_module_exposure_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
```

#### Pattern B — scoped per account/project

```python
from cartography.util import run_scoped_analysis_job

def _sync_one_account(neo4j_session, account_id, update_tag, common_job_parameters):
    common_job_parameters["ACCOUNT_ID"] = account_id

    sync_resources(neo4j_session, account_id, update_tag, common_job_parameters)

    run_scoped_analysis_job(
        "your_module_account_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
```

#### Pattern C — conditional with dependency checking

```python
from cartography.util import run_analysis_and_ensure_deps

def _perform_analysis(requested_syncs, neo4j_session, common_job_parameters):
    run_analysis_and_ensure_deps(
        "your_module_combined_analysis.json",
        {"ec2:instance", "ec2:security_group"},  # required upstream syncs
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )
```

### Step 6 — Test it

Add an integration test that:

1. Calls `sync()` with mocked external boundaries.
2. Asserts the analysis-produced edges / properties using `check_nodes` / `check_rels`.

See the `create-module` skill for testing conventions.

## Best practices

1. **Right scope.** Global runs after all accounts; scoped runs per-account.
2. **Use dep-checking** (`run_analysis_and_ensure_deps`) when a job requires upstream modules.
3. **Document queries** with `__comment__`.
4. **Test analysis jobs** with integration tests.
5. **Use iterative queries** for large datasets.
6. **Clean up stale data** the job creates.

## Common issues

- Job runs before the upstream module — switch to `run_analysis_and_ensure_deps` with the right deps.
- Iterative query never terminates — make sure it returns `COUNT(*) AS TotalCompleted` and the matched set shrinks each iteration.
- Wrong scope — global query reading per-account state can be empty if it runs in the wrong place.

For broader troubleshooting, see the `troubleshooting` skill.

## References (load on demand)

- `references/examples.md` — GCP, AWS, Semgrep wiring examples plus the audit table of modules with proper analysis-job integration.
