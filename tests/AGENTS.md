# Cartography Test Guide

Use this guide for changes under `tests/`. The root `AGENTS.md` covers general
Cartography model and sync patterns; this file is the source of truth for
test-specific expectations.

## Test Intent

Start with a representative sync test that demonstrates the provider's expected
graph relationships. Additional tests must earn their maintenance cost through a
concrete reason: a regression, a known failure-prone boundary, or distinctive
provider behavior. Do not add tests opportunistically because a helper exists, a
branch is uncovered, or a generic failure is imaginable.

A reader should understand why a test belongs in this module. For a non-obvious
regression test, briefly explain the failure or reference the relevant issue; do
not invent a failure history. Prefer a small, focused test set over exhaustive
scenario matrices or one oversized test.

At every test layer, assert observable outcomes rather than implementation
details. Avoid exact request kwargs, mock call counts, internal call order,
incidental result ordering, and intermediate dictionary layouts. Do not enumerate
HTTP statuses merely to verify that `requests` raises an exception.

## Test Layering

- Put fake provider/API payloads in `tests/data` when they are reused or large.
- Put justified unit tests under `tests/unit/cartography/intel/...` and graph
  integration tests under `tests/integration/cartography/intel/...`.
- Do not scaffold API, transform, helper, or CLI tests for every module. Simple
  mappings already exercised by a sync test need no separate transform test.
  A CLI test can cover configuration wiring bypassed by direct `Config`
  construction, but is not a per-module requirement.
- Once a test is justified, choose the narrowest layer that proves its contract.
  Do not repeat the same behavior at transform, loader, and sync layers.

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

- Use `check_rels()` from `tests.integration.util` for integration assertions:
  expected relationships establish that their endpoints exist and are connected
  correctly. Do not routinely pair them with `check_nodes()` assertions.
- Reserve `check_nodes()` or property-specific queries for a concrete
  property-related requirement or issue, such as an analysis whose output is a
  computed property rather than an edge.
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
- Use the shared fixture lifecycle for isolation. Add custom reset/reseed setup
  only for a concrete isolation need; never depend on leftovers from other tests.

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

## Test Ownership

- Module tests establish provider-specific ingestion behavior, not the shared
  data model's guarantees. Standard cleanup is tested by the data model; do not
  add provider cleanup tests unless addressing a specific issue there.
- Do not repeat generic idempotency, collision, or partial-failure scenarios for
  every provider. Test shared behavior at its owning layer; add module-specific
  cases only when a concrete issue or distinctive behavior warrants them.
- For rule tests, keep `cypher_query`, `cypher_count_query`, and any visual query
  semantics aligned: count queries should count the intended eligible or failing
  population for that rule, and visual queries should not silently diverge.

## Fixtures

- Prefer `tests.data.*` helpers or direct repo-relative fixture paths over
  brittle path math such as fixed `parents[N]` indexing.
- Avoid copy-pasting large inline JSON/YAML fixtures when a shared fixture or
  generated structure would make drift less likely.
- Keep fixture data deterministic and minimal for the behavior being tested.
- Do not create module-specific clearing fixtures that enumerate node labels
  (for example, `clear_zendesk`). Adding a resource should not require updating a
  second list of the module's node types. Reuse shared test infrastructure.

## Running Tests

- Follow `docs/root/dev/developer-guide.md` for local setup.
- Run in the uv-managed virtual environment. Prefer the Make targets for full
  local validation:

```bash
make test_lint
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

- For focused lint, including new files not yet tracked by Git, use
  `uv run --frozen pre-commit run --files <changed-files>`.
