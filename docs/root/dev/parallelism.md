# Parallelism and incremental sync

Cartography writes provider data to a shared graph. Parallel execution can
change API usage, graph identity, cleanup, retries, and checkpoints. Review it
as a data correctness change, not only as a performance change.

## Favor predictable behavior

Cartography favors correctness, repeatable cleanup, and deterministic graph
output over maximum throughput. Recent project changes support this direction:

- Declarative data models define graph identity and relationships in one place.
- Generated schema documentation stays aligned with those models.
- Typed analysis jobs make graph enrichment explicit and testable.

AI-assisted development can increase the pace of change. It also makes explicit
contracts more important. Security teams must be able to trust that the same
provider state produces the same graph and that a partial failure does not
remove valid data.

Use built-in parallelism only when it preserves these guarantees. Performance
improvements must not make the default execution model harder to understand or
operate.

## Keep top-level syncs sequential

Keep account, organization, project, and module sync pipelines sequential by
default. Do not run complete `get` → `transform` → `load` → `cleanup` pipelines
in parallel inside Cartography.

Complete pipelines can share:

- Provider API quotas.
- Neo4j connection pools.
- Nodes and relationships.
- Cleanup scopes.
- Analysis jobs.
- Incremental checkpoints.
- Mutable sync state.

Fixing one known race does not prove that a complete pipeline is safe. A new
top-level concurrency model requires a separate design discussion.

Cartography is also a library. Advanced operators can build parallel execution
around it when they understand their environment and can control:

- Provider API quotas and rate limits.
- The connection and transaction capacity of their Neo4j deployment.
- Network, storage, memory, and compute limits.
- Retry, cancellation, and failure isolation.
- Graph ownership and cleanup scopes.

Concurrent runs against the same graph must not own overlapping cleanup scopes.
The operator, not the library, owns this deployment-level concurrency policy.

## Limit parallelism to provider reads

Parallelism can be appropriate in a narrow provider fetch function. Use it only
when all of the following conditions apply:

- Measurements show that provider reads are the bottleneck.
- The provider does not offer a suitable bulk or aggregated API.
- Each work item is independent.
- Workers only call the provider and return data.
- Workers do not write to Neo4j or run cleanup, analysis, or checkpoint updates.
- The worker count has a small, explicit upper bound.
- A worker count of one uses the sequential path.
- The call path does not create nested worker pools.
- Results are combined deterministically before Cartography loads them.
- A failed worker makes the fetch incomplete.

Use this execution boundary:

```text
bounded provider reads → combine results → load → cleanup → analysis/checkpoint
```

Run `load`, cleanup, analysis, and checkpoint updates on the calling thread after
all required fetches succeed.

## Bound the worker count

Do not set the worker count based only on the number of accounts, organizations,
projects, regions, or resources. Use a conservative maximum and clamp it to the
number of work items:

```python
worker_count = max(1, min(max_workers, len(items)))
```

If `worker_count` is one, use the sequential path. This behavior makes the
module easier to test and lets operators disable concurrency without using a
different implementation.

Add a configurable worker count in a dedicated pull request. Document its
default, maximum, provider quota impact, and interaction with other concurrent
work.

## Keep Neo4j writes sequential

Do not share a Neo4j session between threads. The Neo4j driver can be shared,
but [sessions are not thread-safe](https://neo4j.com/docs/python-manual/current/transactions/).

Separate sessions do not make concurrent writes safe. Workers can still write
the same graph identity or run overlapping cleanup jobs. In addition,
concurrent `MERGE` operations do not guarantee node uniqueness without a
[uniqueness constraint](https://neo4j.com/docs/cypher-manual/current/clauses/merge/).

Keep graph writes sequential unless a dedicated design proves that:

- Write scopes do not overlap.
- Shared node identities cannot race.
- Cleanup scopes do not overlap.
- Failure and retry behavior is deterministic.
- Integration tests cover the behavior against Neo4j.

## Fail before cleanup

Parallel fetching must preserve Cartography's fail-before-cleanup contract. If
any required worker fails:

1. Mark the fetch as incomplete.
2. Do not treat the collected data as a complete inventory.
3. Do not run cleanup for the affected scope.
4. Do not advance an incremental checkpoint.
5. Preserve enough context to retry the failed work.

Do not return partial data unless the caller receives an explicit completeness
signal and suppresses cleanup.

## Review incremental sync separately

Incremental sync reduces the data fetched while preserving one execution flow.
It is not a concurrency model. Review incremental sync and parallelism in
separate pull requests.

An incremental sync must:

- Advance its checkpoint only after every dependent stage succeeds.
- Preserve nodes and relationships skipped because they are unchanged.
- Distinguish unchanged data from missing or failed data.
- Suppress cleanup after partial provider responses.
- Retry safely after interruption.
- Produce the same graph as a complete sync for the same provider state.

## Test the execution boundary

Add the smallest tests that prove the new behavior:

- One worker and multiple workers return equivalent results.
- The worker count does not exceed its configured limit.
- Results remain deterministic when workers finish in a different order.
- A worker failure produces an incomplete result.
- Incomplete results do not run cleanup or advance checkpoints.
- Two update tags preserve unchanged data and remove stale data.
- Shared provider identities do not create duplicate graph nodes.
- The sequential path remains covered.

Use an integration test when the behavior affects graph writes, identity,
relationships, cleanup, or checkpoints.

## Keep the pull request focused

Submit concurrency changes separately from incremental sync, unrelated features,
and bug fixes. Include the following information in the pull request:

- Measurements that identify the bottleneck.
- The proposed concurrency boundary.
- The worker limit and default.
- Provider quota and rate-limit considerations.
- Failure, cancellation, cleanup, and checkpoint behavior.
- Focused test evidence.
