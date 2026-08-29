# Sync pattern reference

## Contents

- Entry point template
- Domain `sync()` template
- GET fetching data
- TRANSFORM shaping data
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
@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_key: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    logger.info("Starting MyResource sync")

    # 1. GET
    logger.debug("Fetching MyResource data from API")
    raw_data = get(api_key, tenant_id)

    # 2. TRANSFORM
    logger.debug("Transforming %d MyResource items", len(raw_data))
    transformed_data = transform(raw_data)

    # 3. LOAD
    load_users(neo4j_session, transformed_data, tenant_id, update_tag)

    # 4. CLEANUP
    logger.debug("Running MyResource cleanup job")
    cleanup(neo4j_session, common_job_parameters)

    logger.info("Completed MyResource sync")


def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
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
    data = get_for_parent(parent_id, config)
    transformed = transform(data)
    load_users(neo4j_session, transformed, parent_id, common_job_parameters["UPDATE_TAG"])
```

## GET fetching data

`get()` should be "dumb": just fetch and let exceptions propagate.

```python
@timeit
@aws_handle_regions  # AWS modules only — handles common AWS errors
def get(api_key: str, tenant_id: str) -> dict[str, Any]:
    payload = {"api_key": api_key, "tenant_id": tenant_id}
    session = Session()
    response = session.post(
        "https://api.yourservice.com/users",
        json=payload,
        timeout=(60, 60),  # (connect_timeout, read_timeout)
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

```python
def transform(api_result: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for user_data in api_result["users"]:
        result.append({
            "id": user_data["id"],                  # required
            "email": user_data["email"],            # required
            "name": user_data.get("name"),          # optional -> None
            "last_login": user_data.get("last_login"),
        })
    return result
```

Use `None` for missing values, not empty strings.

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
