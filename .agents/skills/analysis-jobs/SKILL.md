---
name: analysis-jobs
description: Add a post-ingestion typed analysis job to a Cartography module to enrich the graph after sync. Use when the user asks to compute internet exposure, propagate inherited permissions, link Human / canonical ontology nodes, score risk, or add cross-resource analysis after data is loaded.
---

# analysis-jobs

Analysis jobs are post-ingestion typed Python definitions under `cartography/analysis/*/analysis.py` that enrich the graph with computed relationships and properties. Custom JSON jobs are still supported for local extensions and legacy cleanup. They run **after** data is loaded and perform cross-node work that cannot be done during the initial load.

## When to use analysis jobs

Use them when you need to:

1. Compute properties that depend on multiple nodes / relationships.
2. Create relationships that span across resource types.
3. Perform transitive closure (e.g. inherited permissions).
4. Enrich data after all resources of a type are loaded.

**Do NOT** use analysis jobs for:

1. Simple node-to-node relationships (use the data model - see `add-relationship`).
2. Properties that can be computed during `transform()`.
3. Relationships already present in the source data.

## Critical rules

1. **Pick the right scope.** Global typed jobs run after all accounts/projects/tenants. Scoped typed jobs run once per account. Both use `run_typed_analysis_job`; the scope lives on `AnalysisJob.scope`. Use dependency checking (`run_typed_analysis_and_ensure_deps`) when a job needs specific upstream modules.
2. **Use iterative queries for large datasets.** They must return `COUNT(*) AS TotalCompleted`.
3. **Document each query** with `__comment__`.
4. **Clean up stale data** that the analysis job creates (don't leave orphan edges between syncs).
5. **Order statements correctly to avoid read windows.**
    - **Properties:** clean up first (`REMOVE n.attr`), then SET. Cleanup of attributes can usually run in a single transaction.
    - **Relationships:** MERGE first, then DELETE stale (`WHERE r.lastupdated <> $UPDATE_TAG`). Iterative DELETE commits per batch, so a leading DELETE of relationships exposes a graph with those edges missing to concurrent readers until the MERGE finishes. MERGE is idempotent and bumps `r.lastupdated`, so the trailing DELETE only targets edges that genuinely no longer have a current basis. Canonical example: `AWS_LAMBDA_ECR` in `cartography/analysis/aws/analysis.py`.

## Instructions

### Step 1 - Pick global vs scoped

| Type    | Runs                                  | Location                            | Helper                          |
| ------- | ------------------------------------- | ----------------------------------- | ------------------------------- |
| Global  | Once after all accounts / projects    | `cartography/analysis/*/analysis.py`  | `run_typed_analysis_job()`            |
| Scoped  | Once per account / project / tenant   | `cartography/analysis/*/analysis.py`  | `run_typed_analysis_job()`            |

Examples:

- Internet exposure that needs to see all security groups across all accounts -> **global**.
- IAM instance profile analysis that runs per AWS account -> **scoped**.

### Step 2 - Author the typed job

```python
AnalysisJob(
    name="Human-readable name for logging",
    short_name="your_module_exposure_analysis",
    statements=(
        AnalysisStatement(
            match="MATCH (n:NodeType) WHERE ...",
            effects=(SetProperty("n", "property", True, label="NodeType"),),
        ),
    ),
)
```

Typed jobs read as:

```text
AnalysisJob(scope=CleanupScopedTo(...))
    -> AnalysisStatement(match="MATCH ...", effects=(...))
        -> SetProperty / AddToSet / AddValuesToSet / AddRelationship / SetRelationshipProperty
```

`label` is required for node-property effects so cleanup knows which label owns the property. Plain strings become quoted Cypher strings. Use `Var("node.property")`, `Param("UPDATE_TAG")`, or `RawCypher("coalesce(...)")` when the value should compile as Cypher.

`CleanupScopedTo(...)` on the job defines the account/project/tenant boundary used by generated cleanup. `scoped_to="source"` or `"target"` on `AddRelationship` chooses which endpoint is attached to that scoped resource; keep the default `source` unless the target node is the scoped resource.

### Step 3 - Write the queries

**Non-iterative** - single execution, OK for queries touching a manageable number of nodes:

```python
AnalysisStatement(
    match="MATCH (instance:GCPInstance) WHERE ...",
    effects=(SetProperty("instance", "exposed_internet", True, label="GCPInstance"),),
)
```

**Iterative raw query** - required for large raw statements. Must return `TotalCompleted`:

```python
AnalysisStatement(
    query="MATCH (n:Node) WHERE n.stale = true WITH n LIMIT $LIMIT_SIZE DELETE n RETURN COUNT(*) AS TotalCompleted",
    iterative=True,
    iterationsize=1000,
)
```

### Step 4 - Available parameters

`common_job_parameters` is forwarded into the query. Typical params:

-- `$UPDATE_TAG` - current sync timestamp.
-- `$LIMIT_SIZE` - set automatically by the iterative runner.
- Module-specific (`$AWS_ID`, `$PROJECT_ID`, ...).

### Step 5 - Wire the call into your module

#### Pattern A - global analysis at end of ingestion

```python
from cartography.util import run_typed_analysis_job
from cartography.analysis.your_module.analysis import YOUR_MODULE_EXPOSURE_ANALYSIS

@timeit
def start_your_module_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    common_job_parameters = {"UPDATE_TAG": config.update_tag}

    for account in accounts:
        _sync_one_account(neo4j_session, account, config.update_tag, common_job_parameters)

    run_typed_analysis_job(
        YOUR_MODULE_EXPOSURE_ANALYSIS,
        neo4j_session,
        common_job_parameters,
    )
```

#### Pattern B - scoped per account/project

```python
from cartography.util import run_typed_analysis_job
from cartography.analysis.your_module.analysis import YOUR_MODULE_ACCOUNT_ANALYSIS

def _sync_one_account(neo4j_session, account_id, update_tag, common_job_parameters):
    common_job_parameters["ACCOUNT_ID"] = account_id

    sync_resources(neo4j_session, account_id, update_tag, common_job_parameters)

    run_typed_analysis_job(
        YOUR_MODULE_ACCOUNT_ANALYSIS,
        neo4j_session,
        common_job_parameters,
    )
```

#### Pattern C - conditional with dependency checking

```python
from cartography.util import run_typed_analysis_and_ensure_deps
from cartography.analysis.your_module.analysis import YOUR_MODULE_COMBINED_ANALYSIS

def _perform_analysis(requested_syncs, neo4j_session, common_job_parameters):
    run_typed_analysis_and_ensure_deps(
        YOUR_MODULE_COMBINED_ANALYSIS,
        {"ec2:instance", "ec2:security_group"},  # required upstream syncs
        set(requested_syncs),
        common_job_parameters,
        neo4j_session,
    )
```

### Step 6 - Test it

Add an integration test that:

1. Calls `sync()` with mocked external boundaries.
2. Asserts the analysis-produced edges / properties using `check_nodes` / `check_rels`.

See the `create-module` skill for testing conventions.

## Best practices

1. **Right scope.** Global runs after all accounts; scoped runs per-account.
2. **Use dep-checking** (`run_typed_analysis_and_ensure_deps`) when a typed job requires upstream modules.
3. **Document queries** with `__comment__`.
4. **Test analysis jobs** with integration tests.
5. **Use iterative queries** for large datasets.
6. **Clean up stale data** the job creates.

## Common issues

- Job runs before the upstream module - switch to `run_analysis_and_ensure_deps` with the right deps.
- Iterative query never terminates - make sure it returns `COUNT(*) AS TotalCompleted` and the matched set shrinks each iteration.
- Wrong scope - global query reading per-account state can be empty if it runs in the wrong place.

For broader troubleshooting, see the `troubleshooting` skill.

## References (load on demand)

- `references/examples.md` - GCP, AWS, Semgrep wiring examples plus the audit table of modules with proper analysis-job integration.
