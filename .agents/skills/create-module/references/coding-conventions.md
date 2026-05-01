# Coding conventions

## Contents

- Error handling: fail loudly
- Type hints (Python 3.9+)
- Logging
- Date handling
- Deprecation conventions
- Manual write queries
- Git / PR

## Error handling: fail loudly

Cartography prefers loud failures so that broken assumptions surface to operators rather than getting silently papered over.

- When a key assumption stops being true, **stop execution** and let the error propagate.
- Lean toward propagating errors instead of `try`/`except` + log + continue.
- For required data, access it directly. Allow natural `KeyError`, `AttributeError`, `IndexError` to signal corruption.
- Never manufacture "safe" default return values for required data.
- Avoid `hasattr()` / `getattr()` for required fields — rely on schemas and tests.

```python
# DON'T
try:
    risky_operation()
except Exception:
    logger.error("Something went wrong")
    pass

# DO
result = risky_operation()
```

### Required vs optional fields

```python
def transform_user(user_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user_data["id"],          # required — let KeyError raise
        "email": user_data["email"],    # required
        "name": user_data.get("display_name"),  # optional -> None
        "phone": user_data.get("phone_number"), # optional -> None
    }
```

## Type hints (Python 3.9+)

```python
# DO — built-in generics
def get_users(api_key: str) -> dict[str, Any]: ...

# DO — union operator
def process_user(user_id: str | None) -> None: ...

# DON'T — typing.Dict, typing.List, typing.Optional
```

## Logging

### Levels

| Level     | Use for                                                                 |
| --------- | ----------------------------------------------------------------------- |
| CRITICAL  | Framework-level failures that cause cascading errors                    |
| ERROR     | Explicit errors raised at the module level                              |
| WARNING   | Transient errors / config issues that don't stop the module             |
| INFO      | High-level milestones and significant summary stats (module start/end)  |
| DEBUG     | Granular job details, empty result sets, raw data                       |

`INFO` is reserved for actionable, high-level events. "Loaded 0 results" or "Graph job executed" are `DEBUG`.

```python
# DO
logger.info("Starting %s ingestion for tenant %s", module_name, tenant_id)
logger.info("Completed %s sync", module_name)
logger.debug("Running cleanup job for %s", schema_name)
logger.debug("Fetched %s results from API", len(results))
logger.debug("Transforming %s items", len(data))

# DON'T
logger.info("Graph job executed")  # -> DEBUG
logger.info("Fetched 0 users")     # -> DEBUG
```

Do not log the number of nodes/relationships loaded — `load()` already does this in `cartography/client/core/tx.py`.

### Format — lazy `%s`

```python
# DO — lazy evaluation
logger.info("Processing %s users for tenant %s", count, tenant_id)
logger.debug("API response: %s", response_data)

# DON'T — f-strings interpolate eagerly
logger.info(f"Processing {count} users for tenant {tenant_id}")
```

## Date handling

Neo4j 4+ supports native Python datetimes and ISO 8601 strings. Pass values through directly:

```python
# DO
"created_at": user_data.get("created_at")
"last_login": user_data.get("last_login")

# DON'T
"created_at": int(dt_parse.parse(user_data["created_at"]).timestamp() * 1000)
```

## Deprecation conventions

- Temporary compatibility shims, legacy aliases, and migration-only edges get a code comment in the form `# DEPRECATED: ... will be removed in v1.0.0`.
- Prefer comment-only deprecation markers for internal compatibility code that should stay quiet during normal runs.
- Use runtime warnings or log warnings only when users actively invoke a deprecated public module or API surface.

## Manual write queries

- Prefer `load()` / `load_matchlinks()` for ingestion; `GraphJob` for cleanup.
- If a hand-written write query is unavoidable, use `run_write_query()` (managed transaction + retries).
- Reserve `neo4j_session.run()` for read queries or intentional low-level paths that cannot use the managed write helpers.

## Git / PR

- All commits use `git commit -s` (DCO).
- PR descriptions follow `.github/pull_request_template.md`.
