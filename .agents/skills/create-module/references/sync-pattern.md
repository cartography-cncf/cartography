# Sync pattern reference

## Contents

- Entry point template
- Domain `sync()` template
- GET fetching data
- TRANSFORM shaping data
- Streaming large collections
- CLI + Config wiring

## Entry point template

```python
import logging

import neo4j

from cartography.config import Config
from cartography.util import timeit
import cartography.intel.your_module.users


logger = logging.getLogger(__name__)


@timeit
def start_your_module_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    """
    Main entry point for your module ingestion.
    """
    if not config.your_module_api_key:
        logger.info("Your module import is not configured - skipping this module.")
        return

    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.your_module_tenant_id,  # if applicable
    }

    cartography.intel.your_module.users.sync(
        neo4j_session,
        config.your_module_api_key,
        config.your_module_tenant_id,
        config.update_tag,
        common_job_parameters,
    )
```

## Domain `sync()` template

```python
from collections.abc import Iterable
from collections.abc import Iterator


@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_key: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting MyResource sync")

    # GET and TRANSFORM one page at a time; LOAD writes the stream in batches.
    load_users(
        neo4j_session,
        (user for page in get(api_key, tenant_id) for user in transform(page)),
        tenant_id,
        update_tag,
    )

    # CLEANUP runs only after every page loaded.
    cleanup(neo4j_session, common_job_parameters)

    logger.info("Completed MyResource sync")


def load_users(
    neo4j_session: neo4j.Session,
    data: Iterable[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    load(
        neo4j_session,
        MyResourceSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,
    )
```

For sub-resource sync (per project/account/region):

```python
def sync_for_parent(
    neo4j_session: neo4j.Session,
    parent_id: str,
    config: Config,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.debug("Syncing MyResource for %s", parent_id)
    load_users(
        neo4j_session,
        (row for page in get_for_parent(parent_id, config) for row in transform(page)),
        parent_id,
        common_job_parameters["UPDATE_TAG"],
    )
```

## GET fetching data

`get()` should be "dumb": just fetch and let exceptions propagate. When the API
paginates, yield each page as it arrives instead of collecting every page into
one list. See [Streaming large collections](#streaming-large-collections).

```python
def get(api_key: str, tenant_id: str) -> Iterator[list[dict[str, Any]]]:
    session = Session()
    session.headers["Authorization"] = f"Bearer {api_key}"
    cursor: str | None = None
    while True:
        response = session.get(
            "https://api.yourservice.com/users",
            params={"tenant_id": tenant_id, "cursor": cursor, "limit": 1000},
            timeout=(60, 60),  # (connect_timeout, read_timeout)
        )
        response.raise_for_status()
        body = response.json()
        yield body["users"]
        cursor = body.get("next_cursor")
        if not cursor:
            return
```

A getter for a small, bounded result, such as a tenant's settings or a single
object, can return it directly and keep `@timeit`:

```python
@timeit
@aws_handle_regions  # AWS modules only — handles common AWS errors
def get_settings(api_key: str, tenant_id: str) -> dict[str, Any]:
    session = Session()
    response = session.get(
        f"https://api.yourservice.com/tenants/{tenant_id}/settings",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=(60, 60),
    )
    response.raise_for_status()
    return response.json()
```

### Key principles

1. **Minimal error handling.** Do not wrap in `try/except` to log status codes — let them propagate.

   ```python
   # DON'T
   def get_users(api_key: str) -> dict[str, Any]:
       try:
           response = requests.get(...)
           response.raise_for_status()
           return response.json()
       except requests.exceptions.HTTPError as e:
           if e.response.status_code == 401:
               logger.error("Invalid API key")
           elif e.response.status_code == 429:
               logger.error("Rate limit exceeded")
           raise

   # DO
   def get_users(api_key: str) -> dict[str, Any]:
       response = requests.get(...)
       response.raise_for_status()
       return response.json()
   ```

2. **Use decorators** for AWS region/throttling handling: `@aws_handle_regions`.

3. **Fail loudly.** Never return `{}` or `None` to paper over errors.

4. **Always set timeouts.** `timeout=(connect, read)` tuple.

## TRANSFORM shaping data

Required fields use direct access; optional fields use `.get()` with `None` default.

`transform()` takes one page and returns its rows, so a unit test can call it on
a plain list and `sync()` can run it on each page as the page arrives.

```python
def transform(page: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for user_data in page:
        result.append({
            "id": user_data["id"],                  # required
            "email": user_data["email"],            # required
            "name": user_data.get("name"),          # optional -> None
            "last_login": user_data.get("last_login"),
        })
    return result
```

Use `None` for missing values, not empty strings.

## Streaming large collections

A sync runs in a process with a fixed memory limit, but the number of records a
tenant returns has no upper bound. Findings, vulnerabilities, Kubernetes objects,
and assets reach hundreds of thousands or millions of records. A module that holds
every raw record in a list, and then a transformed copy of each, needs memory in
proportion to the tenant and runs out of memory before its first write. Write any
getter whose result grows with the tenant so that memory stays flat:

1. **Yield pages from paginated getters.** Return `Iterator[list[dict]]`, one
   page at a time, instead of a list that holds every page. Don't put
   `@aws_handle_regions` on a generator: the decorator handles errors only while
   the function runs, and a generator's body runs later, inside `load()`.
   Decorate a helper that fetches one page, and call it from the generator.
2. **Transform one page at a time, and pass a generator to `load()`.** `load()`
   and `load_matchlinks()` accept any iterable and write it in transactions of
   `batch_size` rows (10,000 by default). A sync then holds one page of raw
   records and one batch of rows at a time.
3. **Fetch only the records you keep.** Use the API's server-side filters, such
   as an active status, instead of fetching everything and dropping records in
   `transform()`. Cleanup removes every node that a sync no longer returns, so
   filter only on what defines the collection you keep. A lookback window or a
   partial scope, such as some of a tenant's projects, makes cleanup delete
   nodes that still exist.
4. **Raise on any page error, and clean up only after the whole stream loads.**
   A generator that fails partway raises out of `load()`, so `sync()` never
   reaches cleanup. Never catch a page error and return the pages fetched so far:
   cleanup would then delete every node on the pages the getter never reached.
5. **Read a stream once.** Don't call `len()` on a generator or iterate it twice.
   `load()` logs the row count. If a later step needs data from the stream, such
   as building users from role bindings, derive it from the transformed rows as
   they pass, or keep a small index keyed by ID instead of the raw records.
6. **Don't put `@timeit` on a lazy getter.** It times only the creation of the
   iterator. Put it on the `load_*()` function, which now covers the fetch and the
   write.
7. **Look up by key instead of rescanning.** When one collection references
   another, such as services that select pods, build a dict keyed by the join
   field once instead of scanning every record for each lookup.
8. **Batch handwritten writes whose matches grow with the data.** One write
   transaction over millions of rows exceeds Neo4j's transaction memory limit
   (`dbms.memory.transaction.total.max`). Use `load()` or `load_matchlinks()`,
   or an `AnalysisStatement` with `match` and `effects` (not `query`),
   `batched_transactions=True`, and a positive `iterationsize`, instead of one
   `run_write_query()` over every row.

Collecting a list is fine when its size is bounded by configuration rather than
by the tenant, such as accounts, regions, projects, or organizations.

In an integration test, patch the paginated getter to return a list of pages:

```python
@patch.object(
    cartography.intel.your_service.users,
    "get",
    return_value=[MOCK_USERS_PAGE_1, MOCK_USERS_PAGE_2],
)
```

## CLI + Config wiring

In `cartography/cli.py`:

```python
PANEL_YOUR_SERVICE = "Your Service Options"

MODULE_PANELS = {
    # ... existing modules ...
    "yourservice": PANEL_YOUR_SERVICE,
}

# Inside _build_app().run():
your_service_api_key_env_var: Annotated[
    Optional[str],
    typer.Option(
        "--your-service-api-key-env-var",
        help="Environment variable name containing Your Service API key.",
        rich_help_panel=PANEL_YOUR_SERVICE,
        hidden=PANEL_YOUR_SERVICE not in visible_panels,
    ),
] = None,
your_service_tenant_id: Annotated[
    Optional[str],
    typer.Option(
        "--your-service-tenant-id",
        help="Your Service tenant ID.",
        rich_help_panel=PANEL_YOUR_SERVICE,
        hidden=PANEL_YOUR_SERVICE not in visible_panels,
    ),
] = None,

# In the run() body:
your_service_api_key = None
if your_service_api_key_env_var:
    your_service_api_key = os.environ.get(your_service_api_key_env_var)

config = cartography.config.Config(
    # ... existing fields ...
    your_service_api_key=your_service_api_key,
    your_service_tenant_id=your_service_tenant_id,
)
```

In `cartography/config.py`:

```python
class Config:
    def __init__(
        self,
        # ... existing fields ...
        your_service_api_key=None,
        your_service_tenant_id=None,
    ):
        # ... existing assignments ...
        self.your_service_api_key = your_service_api_key
        self.your_service_tenant_id = your_service_tenant_id
```
