---
name: create-module
description: Author a new Cartography intel module end-to-end (entry point, sync GET/TRANSFORM/LOAD/CLEANUP, declarative data model, integration test, schema docs). Use when the user asks to add a new provider, integration, intel module, or service ingestion to Cartography (e.g. "add a new module for service X", "integrate ServiceY", "create a sync for Z API").
---

# create-module

Build a brand new Cartography intel module from scratch using the modern declarative data model. The module must follow the standard sync pattern (`get` -> `transform` -> `load` -> `cleanup`) and be exercised by an integration test.

## Critical rules

1. **Use the data model**, not handwritten Cypher. Call `load()` / `load_matchlinks()` from `cartography.client.core.tx`, and `GraphJob.from_node_schema()` for cleanup.
2. **Sub-resource relationships always point to a tenant-like node** (AWSAccount, AzureSubscription, GCPProject, GitHubOrganization, your `<Service>Tenant`). Never to an infrastructure parent.
3. **Required fields use direct dict access**, optional fields use `.get()` with `None` default. Do not silently swallow exceptions in `get()`.
4. **Only standard schema fields**: any custom field added to a `CartographyNodeSchema` / `CartographyRelSchema` subclass is ignored. See the `add-node-type` and `add-relationship` skills.
5. **Integration tests must call `sync()`**, not individual `load()` calls. Mock only external boundaries (API clients, credentials).
6. **All commits use `git commit -s`** (DCO).

## Instructions

### Step 1 — Lay out the module

```
cartography/intel/your_service/
├── __init__.py          # Entry point: start_your_service_ingestion()
└── users.py             # Domain sync (or devices.py, projects.py, etc.)

cartography/models/your_service/
├── tenant.py            # Tenant/account schema
└── user.py              # Domain schemas

tests/data/your_service/
└── users.py             # Mock API payloads

tests/integration/cartography/intel/your_service/
└── test_users.py        # End-to-end sync test
```

The entry point (`__init__.py`) reads from `Config`, validates required credentials, builds `common_job_parameters`, and dispatches to per-domain `sync()` functions. See `references/sync-pattern.md` for a copy-paste template.

### Step 2 — Wire CLI + Config

In `cartography/cli.py`:
- Add `PANEL_YOUR_SERVICE = "Your Service Options"` and register it in `MODULE_PANELS`.
- Add Typer options inside `_build_app().run()` (use `Annotated[Optional[str], typer.Option(...)]` with `rich_help_panel=PANEL_YOUR_SERVICE`).
- Resolve secrets from `os.environ` and pass them into `cartography.config.Config(...)`.

In `cartography/config.py`, extend `Config.__init__` with the new fields. Then in your module entry point, validate them and short-circuit with `logger.info("... not configured - skipping module")` when missing.

### Step 3 — Implement the sync pattern

For each domain (users, devices, projects, ...):

```python
@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_key: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    raw = get(api_key, tenant_id)               # 1. GET — dumb, raises on failure
    data = transform(raw)                       # 2. TRANSFORM — shape for ingest
    load_users(neo4j_session, data, tenant_id, update_tag)  # 3. LOAD — data model
    cleanup(neo4j_session, common_job_parameters)           # 4. CLEANUP — GraphJob
```

`get()` should be minimal: set timeouts, call `response.raise_for_status()`, and let errors propagate. AWS get-functions wrap with `@aws_handle_regions`. See `references/sync-pattern.md` for the long-form template, error-handling rules, and transform examples.

### Step 4 — Define the data model

Create dataclasses in `cartography/models/your_service/`. Required for every node:

```python
@dataclass(frozen=True)
class YourServiceUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")                                    # REQUIRED
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)  # REQUIRED
    # business properties...
    tenant_id: PropertyRef = PropertyRef("TENANT_ID", set_in_kwargs=True)
```

The schema picks a label, properties, and the mandatory `sub_resource_relationship` to your tenant-like node:

```python
@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
    other_relationships: OtherRelationships = OtherRelationships([
        YourServiceUserToHumanRel(),
    ])
```

For advanced node configurations (extra labels, conditional labels, scoped cleanup, one-to-many) see the `add-node-type` skill. For relationships, MatchLinks, and multi-module patterns see the `add-relationship` skill. See `references/data-model.md` for the full reference.

### Step 5 — Load + cleanup

```python
def load_users(neo4j_session, data, tenant_id, update_tag):
    load(neo4j_session, YourServiceTenantSchema(), [{"id": tenant_id}], lastupdated=update_tag)
    load(neo4j_session, YourServiceUserSchema(), data, lastupdated=update_tag, TENANT_ID=tenant_id)

def cleanup(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(YourServiceUserSchema(), common_job_parameters).run(neo4j_session)
```

If you hand-write a Cypher write query during prototyping, use `run_write_query()` (managed transaction + retries), never `neo4j_session.run()`.

### Step 6 — Integration test

In `tests/integration/cartography/intel/your_service/test_users.py`, patch only `get()` and call `sync()` end-to-end. Assert outcomes (nodes + relationships) using `tests.integration.util.check_nodes` / `check_rels`. Do not assert on mock call counts or internal parameters. See `references/testing.md` for a full template and the test boundary policy.

### Step 7 — Schema documentation

Add a page at `docs/root/modules/your_service/schema.md`. Use `###` for node names, `####` for the "Relationships" subsection, **bold** indexed/primary fields. If the node has a semantic label, add the standard ontology mapping blockquote (see the `enrich-ontology` skill).

### Step 8 — Optional: analysis jobs

If the module needs post-ingestion enrichment (internet exposure, permission inheritance, cross-resource linking), call `run_analysis_job()` / `run_scoped_analysis_job()` at the end of the entry point. See the `analysis-jobs` skill.

### Step 9 — Pre-submission checks

```bash
make lint
# integration test for the module:
pytest tests/integration/cartography/intel/your_service/ -x
```

Sign every commit: `git commit -s -m "..."`. Update the PR description to match `.github/pull_request_template.md`.

## Final checklist

- [ ] Entry point validates config and skips cleanly when unconfigured
- [ ] CLI panel + `Config` fields wired, secrets resolved from env vars
- [ ] Sync follows GET -> TRANSFORM -> LOAD -> CLEANUP
- [ ] All schemas use only standard fields (`label`, `properties`, `sub_resource_relationship`, `other_relationships`, `extra_node_labels`, `scoped_cleanup`)
- [ ] Sub-resource relationship targets a tenant-like node
- [ ] Required fields use `data["x"]`, optional use `data.get("x")` with `None` default
- [ ] `extra_index=True` set on frequently queried fields
- [ ] Integration test exercises `sync()`, asserts nodes + rels with `check_nodes` / `check_rels`
- [ ] Schema doc added under `docs/root/modules/your_service/schema.md`
- [ ] `make lint` clean, `git commit -s` used

## Common issues

See the `troubleshooting` skill for `ModuleNotFoundError`, `PropertyRef validation failed`, missing relationships, cleanup misbehavior, and date-handling pitfalls.

## References (load on demand)

- `references/sync-pattern.md` — full templates for `__init__.py`, `sync()`, `get()`, `transform()`, error-handling rules.
- `references/data-model.md` — node properties, schema, sub-resource relationships, loading, ECS example.
- `references/testing.md` — integration test template, `check_nodes` / `check_rels`, mocking policy, integration test boundary.
- `references/coding-conventions.md` — error handling, type hints, logging levels and format, deprecation conventions.
