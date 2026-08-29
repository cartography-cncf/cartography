# Cartography Test Guide

Use this guide for changes under `tests/`. The root `AGENTS.md` covers general
Cartography model and sync patterns; this file is the source of truth for
test-specific expectations.

## Test Layering

- Put fake provider/API payloads in `tests/data` when they are reused or large.
- Add unit tests under `tests/unit/cartography/intel/...` for pure transforms,
  input normalization, error classification, and small helper behavior.
- Add integration tests under `tests/integration/cartography/intel/...` when the
  behavior depends on Neo4j writes, relationship creation, cleanup, analysis
  jobs, or idempotency across update tags.
- Prefer the narrowest test layer that proves the contract. Do not add a broad
  integration test for behavior that a unit test can prove directly.

## Integration Test Boundary

- Integration tests should exercise real Cartography `sync()`, `sync_*()`,
  loader, cleanup, `GraphJob`, and analysis-job flows whenever practical.
- Prefer the complete `sync()` / `sync_*()` path for end-to-end module behavior.
- Lower-level loader or cleanup helpers are acceptable when the test is
  intentionally about a split ingestion phase, idempotency, migration, or cleanup
  contract that is hard to isolate through the top-level sync path.
- Mock only external boundaries in integration tests: provider API clients,
  service discovery, credentials, network/file responses, and other inputs from
  outside Cartography.
- Do not mock Cartography internal sync, transform, load, cleanup, or analysis
  functions in integration tests unless the test is explicitly about
  orchestration and cannot be expressed through real internal calls.

## Graph Setup And Assertions

- Use `check_nodes()` and `check_rels()` from `tests.integration.util` for simple
  node and relationship assertions.
- Direct read queries with `neo4j_session.run()` are fine for assertions that
  need counts, labels, relationship properties, negative matches, or other shapes
  that `check_nodes()` / `check_rels()` do not express clearly.
- Direct Cypher writes may be used for minimal prerequisite setup, graph reset,
  reseeding shared fixtures, or teardown when no practical Cartography loader
  exists for that setup.
- Prefer Cartography loaders, `GraphJob`, `run_analysis_job()`, and
  `run_scoped_analysis_job()` over handwritten write queries for production
  graph mutations.
- If a handwritten write query is necessary outside prerequisite setup or
  teardown, use `run_write_query()` so the write runs with Cartography's
  transaction retry handling, and keep the reason obvious in the test.
- Reset and reseed graph state before sync tests that depend on scoped data; do
  not let tests pass because of leftovers from module-scoped fixtures or earlier
  tests.

## Test Structure

- Structure each test with `# Arrange`, `# Act`, and `# Assert` comments to mark
  the three phases. This makes it obvious where setup ends, where the behavior
  under test is exercised, and where the assertions begin.
- `# Arrange` covers fixture loading, mock setup, seeding the graph, and any
  prerequisite state. `# Act` is the single call to the function under test
  (e.g. `sync()`, `load_*()`, `transform_*()`, `cleanup_*()`). `# Assert` covers
  `check_nodes()`, `check_rels()`, and any direct read queries.
- Combine phases as `# Act and assert` only when the action and assertion are a
  single expression (for example, `pytest.raises(...)` around the call).
- Keep each phase contiguous; avoid interleaving setup between assertions. If a
  test naturally splits into multiple act/assert cycles (e.g. two update tags
  for an idempotency or cleanup test), repeat the comments for each cycle so the
  structure stays readable.

## Coverage Expectations

- Assert both node existence and the relationships that make the data traversable.
- For cleanup/idempotency changes, test the stale-data path as well as the
  current-data path, usually with at least two update tags.
- For scoped cleanup or partial-failure behavior, test that successful scopes are
  cleaned up and incomplete scopes preserve prior data when that is the contract.
- For generated IDs or canonicalization, include cases that would collide or
  drift without the intended stable identity input.
- For rule tests, keep `cypher_query`, `cypher_count_query`, and any visual query
  semantics aligned: count queries should count the intended eligible or failing
  population for that rule, and visual queries should not silently diverge.
- Add negative/error-path coverage when the new behavior changes operator-facing
  failure handling, cleanup safety, or skipped-input behavior.

## Fixtures

- Prefer `tests.data.*` helpers or direct repo-relative fixture paths over
  brittle path math such as fixed `parents[N]` indexing.
- Avoid copy-pasting large inline JSON/YAML fixtures when a shared fixture or
  generated structure would make drift less likely.
- Keep fixture data deterministic and minimal, but include enough fields to prove
  relationships, cleanup scope, and ID stability.

## Running Tests

- Follow `docs/root/dev/developer-guide.md` for local setup.
- Prefer the Make targets for full local validation:

```bash
make test_unit
make test_integration
make test
```

- `tests/integration/conftest.py` starts a Neo4j testcontainer automatically
  when `NEO4J_URL` is not set. Docker must be available for this path.
- Set `NEO4J_URL` only when you intentionally want integration tests to use an
  existing Neo4j instance.
- Integration tests delete graph data from the Neo4j database they use. When
  setting `NEO4J_URL`, point it at a disposable database.
- Focused pytest commands are fine while iterating, for example:

```bash
uv run pytest tests/integration/cartography/intel/aws/test_iam.py::test_load_groups
```
