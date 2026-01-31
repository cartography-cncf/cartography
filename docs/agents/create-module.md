# Creating a New Cartography Module

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Add Node Type](add-node-type.md) | [Add Relationship](add-relationship.md) | [Analysis Jobs](analysis-jobs.md)

This guide walks you through creating a new Cartography intel module from scratch, covering the complete sync pattern, data model definitions, and testing.

## Table of Contents

1. [Module Structure](#module-structure) - File organization and entry points
2. [The Sync Pattern](#the-sync-pattern-get-transform-load-cleanup) - GET, TRANSFORM, LOAD, CLEANUP
3. [Data Model](#data-model-defining-nodes-and-relationships) - Nodes, properties, and relationships
4. [Configuration and Credentials](#configuration-and-credentials) - CLI args and validation
5. [Testing Your Module](#testing-your-module) - Integration tests and test data
6. [Schema Documentation](#schema-documentation) - Documenting your schema
7. [Coding Conventions](#coding-conventions) - Error handling, type hints, logging
8. [Common Pitfalls](#common-pitfalls) - Troubleshooting common issues
9. [Final Checklist](#final-checklist) - Pre-submission checklist

## Module Structure

Every Cartography intel module follows this structure:

```
cartography/intel/your_module/
├── __init__.py          # Main entry point with sync orchestration
├── users.py             # Domain-specific sync modules (users, devices, etc.)
├── devices.py           # Additional domain modules as needed
└── ...

cartography/models/your_module/
├── user.py              # Data model definitions
├── tenant.py            # Tenant/account model
└── ...
```

### Main Entry Point (`__init__.py`)

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
    Main entry point for your module ingestion
    """
    # Validate configuration
    if not config.your_module_api_key:
        logger.info("Your module import is not configured - skipping this module.")
        return

    # Set up common job parameters for cleanup
    common_job_parameters = {
        "UPDATE_TAG": config.update_tag,
        "TENANT_ID": config.your_module_tenant_id,  # if applicable
    }

    # Call domain-specific sync functions
    cartography.intel.your_module.users.sync(
        neo4j_session,
        config.your_module_api_key,
        config.your_module_tenant_id,
        config.update_tag,
        common_job_parameters,
    )
```

## The Sync Pattern: Get, Transform, Load, Cleanup

Every sync function follows this exact pattern:

```python
@timeit
def sync(
    neo4j_session: neo4j.Session,
    api_key: str,
    tenant_id: str,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Main sync entry point for the module.
    """
    logger.info("Starting MyResource sync")

    # 1. GET - Fetch data from API
    logger.debug("Fetching MyResource data from API")
    raw_data = get(api_key, tenant_id)

    # 2. TRANSFORM - Shape data for ingestion
    logger.debug("Transforming %d MyResource items", len(raw_data))
    transformed_data = transform(raw_data)

    # 3. LOAD - Ingest to Neo4j using data model
    load_users(neo4j_session, transformed_data, tenant_id, update_tag)

    # 4. CLEANUP - Remove stale data
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


def sync_for_parent(
    neo4j_session: neo4j.Session,
    parent_id: str,
    config: Config,
    common_job_parameters: dict[str, Any],
) -> None:
    """
    Sync resources for a specific parent (e.g., project, account, region).
    """
    logger.debug("Syncing MyResource for %s", parent_id)

    data = get_for_parent(parent_id, config)

    logger.debug("Transforming %d MyResource for %s", len(data), parent_id)
    transformed = transform(data)

    load_users(neo4j_session, transformed, parent_id, common_job_parameters["UPDATE_TAG"])
```

### GET: Fetching Data

The `get` function should be "dumb" - just fetch data and raise exceptions on failure:

```python
@timeit
@aws_handle_regions  # Handles common AWS errors like region availability, only for AWS modules.
def get(api_key: str, tenant_id: str) -> dict[str, Any]:
    """
    Fetch data from external API
    Should be simple and raise exceptions on failure
    """
    payload = {
        "api_key": api_key,
        "tenant_id": tenant_id,
    }

    session = Session()
    response = session.post(
        "https://api.yourservice.com/users",
        json=payload,
        timeout=(60, 60),  # (connect_timeout, read_timeout)
    )
    response.raise_for_status()  # Raise exception on HTTP error
    return response.json()
```

**Key Principles for `get()` Functions:**

1. **Minimal Error Handling**: Avoid adding try/except blocks in `get()` functions. Let errors propagate up to the caller.
   ```python
   # DON'T: Add complex error handling in get()
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
       except requests.exceptions.RequestException as e:
           logger.error(f"Network error: {e}")
           raise

   # DO: Keep it simple and let errors propagate
   def get_users(api_key: str) -> dict[str, Any]:
       response = requests.get(...)
       response.raise_for_status()
       return response.json()
   ```

2. **Use Decorators**: For AWS modules, use `@aws_handle_regions` to handle common AWS errors:
   ```python
   @timeit
   @aws_handle_regions  # Handles region availability, throttling, etc.
   def get_ec2_instances(boto3_session: boto3.session.Session, region: str) -> list[dict[str, Any]]:
       client = boto3_session.client("ec2", region_name=region)
       return client.describe_instances()["Reservations"]
   ```

3. **Fail Loudly**: If an error occurs, let it propagate up to the caller. This helps users identify and fix issues quickly:
   ```python
   # DON'T: Silently continue on error
   def get_data() -> dict[str, Any]:
       try:
           return api.get_data()
       except Exception:
           return {}  # Silently continue with empty data

   # DO: Let errors propagate
   def get_data() -> dict[str, Any]:
       return api.get_data()  # Let errors propagate to caller
   ```

4. **Timeout Configuration**: Set appropriate timeouts to avoid hanging:
   ```python
   # DO: Set timeouts
   response = session.post(
       "https://api.service.com/users",
       json=payload,
       timeout=(60, 60),  # (connect_timeout, read_timeout)
   )
   ```

### TRANSFORM: Shaping Data

Transform data to make it easier to ingest. Handle required vs optional fields carefully:

```python
def transform(api_result: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transform API data for Neo4j ingestion
    """
    result: list[dict[str, Any]] = []

    for user_data in api_result["users"]:
        transformed_user = {
            # Required fields - use direct access (will raise KeyError if missing)
            "id": user_data["id"],
            "email": user_data["email"],

            # Optional fields - use .get() with None default
            "name": user_data.get("name"),
            "last_login": user_data.get("last_login"),
        }
        result.append(transformed_user)

    return result
```

**Key Principles:**
- **Required fields**: Use `data["field"]` - let it fail if missing
- **Optional fields**: Use `data.get("field")` - defaults to `None`
- **Consistency**: Use `None` for missing values, not empty strings

## Data Model: Defining Nodes and Relationships

Modern Cartography uses a declarative data model. Here's how to define your schema:

### Node Properties

Define the properties that will be stored on your node:

```python
from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties

@dataclass(frozen=True)
class YourServiceUserNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("id")

    # Automatic fields (set by cartography)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields from your API
    email: PropertyRef = PropertyRef("email", extra_index=True)  # Create index for queries
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    last_login: PropertyRef = PropertyRef("last_login")
    is_admin: PropertyRef = PropertyRef("is_admin")

    # Fields from kwargs (same for all records in a batch)
    tenant_id: PropertyRef = PropertyRef("TENANT_ID", set_in_kwargs=True)
```

**PropertyRef Parameters:**
- First parameter: Key in your data dict or kwarg name. Use keys when you are ingesting a list of records. Use kwargs when you want to set the same value for all records in the list of records.
- `extra_index=True`: Create database index for better query performance
- `set_in_kwargs=True`: Value comes from kwargs passed to `load()`, not from individual records

> For advanced node configurations (extra labels, ontology integration), see [Adding a New Node Type](add-node-type.md).

### Node Schema

Define your complete node schema:

```python
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import OtherRelationships


@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"                              # Neo4j node label
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()

    # Optional: Additional relationships
    other_relationships: OtherRelationships = OtherRelationships([
        YourServiceUserToHumanRel(),  # Connect to Human nodes
    ])
```

### Sub-Resource Relationships: Always Point to Tenant-Like Objects

The `sub_resource_relationship` should **always** refer to a tenant-like object that represents the ownership or organizational boundary of the resource. This is crucial for proper data organization and cleanup operations.

**Correct Examples:**
- **AWS Resources**: Point to `AWSAccount` (tenant = AWS account)
- **Azure Resources**: Point to `AzureSubscription` (tenant = Azure subscription)
- **GCP Resources**: Point to `GCPProject` (tenant = GCP project)
- **SaaS Applications**: Point to `YourServiceTenant` (tenant = organization/company)
- **GitHub Resources**: Point to `GitHubOrganization` (tenant = GitHub org)

**Incorrect Examples:**
- Pointing to a parent resource that's not tenant-like (e.g., `ECSTaskDefinition` -> `ECSTask`)
- Pointing to infrastructure components (e.g., `ECSContainer` -> `ECSTask`)
- Pointing to logical groupings that aren't organizational boundaries

**Example: AWS ECS Container Definitions**

```python
# CORRECT: Container definitions belong to AWS accounts
@dataclass(frozen=True)
class ECSContainerDefinitionSchema(CartographyNodeSchema):
    label: str = "ECSContainerDefinition"
    properties: ECSContainerDefinitionNodeProperties = ECSContainerDefinitionNodeProperties()
    sub_resource_relationship: ECSContainerDefinitionToAWSAccountRel = ECSContainerDefinitionToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([
        ECSContainerDefinitionToTaskDefinitionRel(),  # Business relationship
    ])

# CORRECT: Relationship to AWS Account (tenant-like)
@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("AWS_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerDefinitionToAWSAccountRelProperties = ECSContainerDefinitionToAWSAccountRelProperties()

# CORRECT: Business relationship to task definition (not tenant-like)
@dataclass(frozen=True)
class ECSContainerDefinitionToTaskDefinitionRel(CartographyRelSchema):
    target_node_label: str = "ECSTaskDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("_taskDefinitionArn"),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONTAINER_DEFINITION"
    properties: ECSContainerDefinitionToTaskDefinitionRelProperties = ECSContainerDefinitionToTaskDefinitionRelProperties()
```

**Why This Matters:**
1. **Cleanup Operations**: Cartography uses the sub-resource relationship to determine which data to clean up during sync operations
2. **Data Organization**: Tenant-like objects provide natural boundaries for data organization
3. **Access Control**: Tenant relationships enable proper access control and data isolation
4. **Consistency**: Following this pattern ensures consistent data modeling across all modules

### Relationships

Define how your nodes connect to other nodes:

```python
from cartography.models.core.relationships import (
    CartographyRelSchema, CartographyRelProperties, LinkDirection,
    make_target_node_matcher, TargetNodeMatcher
)

# Relationship properties (usually just lastupdated)
@dataclass(frozen=True)
class YourServiceTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

# The relationship itself
@dataclass(frozen=True)
class YourServiceTenantToUserRel(CartographyRelSchema):
    target_node_label: str = "YourServiceTenant"                # What we're connecting to
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("TENANT_ID", set_in_kwargs=True),     # Match on tenant.id = TENANT_ID kwarg
    })
    direction: LinkDirection = LinkDirection.INWARD             # Tenant points to User
    rel_label: str = "RESOURCE"                                 # Relationship label
    properties: YourServiceTenantToUserRelProperties = YourServiceTenantToUserRelProperties()
```

**Relationship Directions:**
- `LinkDirection.INWARD`: `(:YourServiceTenant)-[:RESOURCE]->(:YourServiceUser)` - Used for sub_resource relationships
- `LinkDirection.OUTWARD`: `(:YourServiceUser)-[:RESOURCE]->(:YourServiceTenant)` - Rarely used for RESOURCE

> For advanced relationship patterns (MatchLinks, one-to-many, cross-module relationships), see [Adding a New Relationship](add-relationship.md).

### Loading Data

Use the `load` function with your schema:

```python
from cartography.client.core.tx import load


def load_users(
    neo4j_session: neo4j.Session,
    data: list[dict[str, Any]],
    tenant_id: str,
    update_tag: int,
) -> None:
    # Load tenant first (if it doesn't exist)
    load(
        neo4j_session,
        YourServiceTenantSchema(),
        [{"id": tenant_id}],
        lastupdated=update_tag,
    )

    # Load users with relationships
    load(
        neo4j_session,
        YourServiceUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,  # This becomes available as PropertyRef("TENANT_ID", set_in_kwargs=True)
    )
```

### Cleanup Jobs

Always implement cleanup to remove stale data:

```python
from cartography.graph.job import GraphJob

def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove nodes that weren't updated in this sync run
    """
    logger.debug("Running Your Service cleanup job")

    # Cleanup users
    GraphJob.from_node_schema(YourServiceUserSchema(), common_job_parameters).run(neo4j_session)
```

### Analysis Jobs (Optional)

For modules that require post-ingestion graph enrichment (e.g., internet exposure analysis, permission inheritance), add analysis job calls at the end of your main ingestion function. See [Adding Analysis Jobs](analysis-jobs.md) for detailed patterns and examples.

```python
from cartography.util import run_analysis_job

@timeit
def start_your_module_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    # ... sync all resources ...

    # Optional: Run analysis jobs after all data is synced
    run_analysis_job(
        "your_module_analysis.json",
        neo4j_session,
        common_job_parameters,
    )
```

## Configuration and Credentials

### Adding CLI Arguments

Add your configuration options in `cartography/cli.py`:

```python
# In add_auth_args function
parser.add_argument(
    '--your-service-api-key-env-var',
    type=str,
    help='Name of environment variable containing Your Service API key',
)

parser.add_argument(
    '--your-service-tenant-id',
    type=str,
    help='Your Service tenant ID',
)
```

### Configuration Object

Add fields to `cartography/config.py`:

```python
@dataclass
class Config:
    # ... existing fields ...
    your_service_api_key: str | None = None
    your_service_tenant_id: str | None = None
```

### Validation in Module

Always validate your configuration:

```python
def start_your_service_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    # Validate required configuration
    if not config.your_service_api_key:
        logger.info("Your Service API key not configured - skipping module")
        return

    if not config.your_service_tenant_id:
        logger.info("Your Service tenant ID not configured - skipping module")
        return

    # Get API key from environment
    api_key = os.getenv(config.your_service_api_key)
    if not api_key:
        logger.error(f"Environment variable {config.your_service_api_key} not set")
        return
```

## Testing Your Module

**Key Principle: Test outcomes, not implementation details.**

Focus on verifying that data is written to the graph as expected, rather than testing internal function parameters or implementation details. Mock external dependencies (APIs, databases) when necessary, but avoid brittle parameter testing.

### Test Data

Create mock data in `tests/data/your_service/`:

```python
# tests/data/your_service/users.py
MOCK_USERS_RESPONSE = {
    "users": [
        {
            "id": "user-123",
            "email": "alice@example.com",
            "display_name": "Alice Smith",
            "created_at": "2023-01-15T10:30:00Z",
            "last_login": "2023-12-01T14:22:00Z",
            "is_admin": False,
        },
        {
            "id": "user-456",
            "email": "bob@example.com",
            "display_name": "Bob Jones",
            "created_at": "2023-02-20T16:45:00Z",
            "last_login": None,  # Never logged in
            "is_admin": True,
        },
    ]
}
```

### Integration Tests

Test actual Neo4j loading in `tests/integration/cartography/intel/your_service/`:

```python
# tests/integration/cartography/intel/your_service/test_users.py
from unittest.mock import patch
import cartography.intel.your_service.users
from tests.data.your_service.users import MOCK_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = "tenant-123"

@patch.object(
    cartography.intel.your_service.users,
    "get",
    return_value=MOCK_USERS_RESPONSE,
)
def test_sync_users(mock_api, neo4j_session):
    """
    Test that users sync correctly and create proper nodes and relationships
    """
    # Act - Use the sync function instead of calling load directly
    cartography.intel.your_service.users.sync(
        neo4j_session,
        "fake-api-key",
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # DO: Test outcomes - verify data is written to the graph as expected
    # Assert - Use check_nodes() instead of raw Neo4j queries.
    expected_nodes = {
        ("user-123", "alice@example.com"),
        ("user-456", "bob@example.com"),
    }
    assert check_nodes(neo4j_session, "YourServiceUser", ["id", "email"]) == expected_nodes

    # Verify tenant was created
    expected_tenant_nodes = {
        (TEST_TENANT_ID,),
    }
    assert check_nodes(neo4j_session, "YourServiceTenant", ["id"]) == expected_tenant_nodes

    # Assert relationships are created correctly.
    # Use check_rels() instead of raw Neo4j queries for relationships
    expected_rels = {
        ("user-123", TEST_TENANT_ID),
        ("user-456", TEST_TENANT_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "YourServiceUser",
            "id",
            "YourServiceTenant",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )
```

**What to Test:**
- **Outcomes**: Nodes created with correct properties
- **Outcomes**: Relationships created between expected nodes

**What NOT to Test:**
- **Implementation**: Function parameters passed to mocks (brittle!)
- **Implementation**: Internal function call order
- **Implementation**: Mock call counts unless absolutely necessary

**When to Mock:**
- External APIs (AWS, Azure, third-party services) - provide test data
- Database connections - avoid real connections
- Network calls - avoid real network requests

**When NOT to Mock:**
- Internal Cartography functions
- Data transformation logic
- The function that is being tested

## Schema Documentation

Always document your schema in `docs/root/modules/your_service/schema.md`. Follow these formatting conventions:

### Documentation Conventions

1. **Title Levels**:
   - Use `###` (h3) for node names
   - Use `####` (h4) for the "Relationships" subsection

2. **Indexed Fields in Bold**:
   - Mark indexed fields (primary key, extra_index=True) with **bold** in the table
   - Example: `|**id**| The unique identifier|`

3. **Ontology Mapping Note** (if applicable):
   - Add a blockquote after the node description for nodes with semantic labels
   - See [Enriching the Ontology](enrich-ontology.md#documenting-ontology-integration) for the standard phrase format

### Example Documentation

```markdown
## Your Service Schema

### YourServiceUser

Represents a user in Your Service.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GSuiteUser).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job first discovered this node |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | Unique user identifier |
| **email** | User email address (indexed for queries) |
| name | User display name |
| created_at | Account creation timestamp |
| last_login | Last login timestamp |
| is_admin | Admin privileges flag |

#### Relationships

- YourServiceUser belong to YourServiceTenant.
    ```cypher
    (:YourServiceTenant)-[:RESOURCE]->(:YourServiceUser)
    ```

- YourServiceUser may be connected to Human nodes.
    ```cypher
    (:Human)-[:IDENTITY_YOUR_SERVICE]->(:YourServiceUser)
    ```
```

## File Structure Template

```
cartography/intel/your_service/
├── __init__.py          # Main entry point
└── entities.py          # Domain sync modules

cartography/models/your_service/
├── entity.py            # Data model definitions
└── tenant.py            # Tenant model

tests/data/your_service/
└── entities.py          # Mock test data

tests/unit/cartography/intel/your_service/
└── test_entities.py     # Unit tests

tests/integration/cartography/intel/your_service/
└── test_entities.py     # Integration tests
```

## Common Pitfalls

### Import Errors

```python
# Problem: ModuleNotFoundError for your new module
# Solution: Ensure __init__.py files exist in all directories
cartography/intel/your_service/__init__.py
cartography/models/your_service/__init__.py
```

### Schema Validation Errors

```python
# Problem: "PropertyRef validation failed"
# Solution: Check dataclass syntax and PropertyRef definitions
@dataclass(frozen=True)  # Don't forget frozen=True!
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")  # Must have type annotation
```

### Relationships Not Created

```python
# Problem: Relationships not created
# Solution: Ensure target nodes exist before creating relationships
# Load parent nodes first:
load(neo4j_session, TenantSchema(), tenant_data, lastupdated=update_tag)
# Then load child nodes with relationships:
load(neo4j_session, UserSchema(), user_data, lastupdated=update_tag, TENANT_ID=tenant_id)
```

### Cleanup Job Failures

```python
# Problem: "GraphJob failed" during cleanup
# Solution: Check common_job_parameters structure
common_job_parameters = {
    "UPDATE_TAG": config.update_tag,  # Must match what's set on nodes
    "TENANT_ID": tenant_id,           # If using scoped cleanup (default)
}
```

### Date Handling

Neo4j 4+ supports native Python datetime objects and ISO 8601 strings:

```python
# DON'T: Manually parse dates or convert to epoch timestamps
"created_at": int(dt_parse.parse(user_data["created_at"]).timestamp() * 1000)

# DO: Pass datetime values directly - Neo4j handles them natively
"created_at": user_data.get("created_at")
"last_login": user_data.get("last_login")
```

### Performance Issues

```python
# Problem: Slow queries
# Solution: Add indexes to frequently queried fields
email: PropertyRef = PropertyRef("email", extra_index=True)

# Note: Fields in target_node_matcher are indexed automatically
```

## Coding Conventions

### Error Handling Principles

#### Fail Loudly When Assumptions Break

Cartography likes to fail loudly so that broken assumptions bubble exceptions up to operators instead of being papered over.

- When key assumptions your code relies upon stop being true, **stop execution immediately** and let the error propagate.
- Lean toward propagating errors up to callers instead of logging a warning inside a `try`/`except` block and continuing.
- If you're confident data should always exist, access it directly. Allow natural `KeyError`, `AttributeError`, or `IndexError` exceptions to signal corruption.
- Never manufacture "safe" default return values for required data.
- Avoid `hasattr()`/`getattr()` for required fields - rely on schemas and tests to detect breakage.

```python
# DON'T: Catch base exceptions and continue silently
try:
    risky_operation()
except Exception:
    logger.error("Something went wrong")
    pass  # Silently continue - BAD!

# DO: Let errors propagate or handle specifically
result = risky_operation()  # Let it fail if something is wrong
```

#### Required vs Optional Field Access

```python
def transform_user(user_data: dict[str, Any]) -> dict[str, Any]:
    return {
        # Required field - let it raise KeyError if missing
        "id": user_data["id"],
        "email": user_data["email"],

        # Optional field - gracefully handle missing data
        "name": user_data.get("display_name"),
        "phone": user_data.get("phone_number"),
    }
```

### Type Hints Style Guide

Use Python 3.9+ style type hints:

```python
# DO: Use built-in type hints (Python 3.9+)
def get_users(api_key: str) -> dict[str, Any]:
    ...

# DO: Use union operator for optional types
def process_user(user_id: str | None) -> None:
    ...

# DON'T: Use objects from typing module (Dict, List, Optional)
```

### Logging Guidelines

#### Log Levels

Use appropriate log levels to reduce noise in production:

| Level | Usage |
|-------|-------|
| `CRITICAL` | Framework-level component failures that cause cascading errors |
| `ERROR` | Explicit errors raised at the module level |
| `WARNING` | Transient errors or configuration issues that do not stop the module |
| `INFO` | High-level milestones (module start/finish) and significant summary statistics |
| `DEBUG` | Everything else: granular job details, empty result sets, raw data |

**Key Principle**: `INFO` should be reserved for actionable, high-level events. Empty states like "Loaded 0 results" or routine operations like "Graph job executed" belong in `DEBUG`.

```python
# DO: Use INFO for significant milestones
logger.info("Starting %s ingestion for tenant %s", module_name, tenant_id)
logger.info("Completed %s sync", module_name)

# DO: Use DEBUG for granular details
logger.debug("Running cleanup job for %s", schema_name)
logger.debug("Fetched %s results from API", len(results))
logger.debug("Transforming %s items", len(data))

# DON'T: Use INFO for routine operations
logger.info("Graph job executed")  # Should be DEBUG
logger.info("Fetched 0 users")     # Should be DEBUG
```

> **Note**: Do not log the number of nodes or relationships loaded. This is handled automatically by the `load()` function in `cartography/client/core/tx.py`.

#### Logging Format

Use lazy evaluation with `%s` formatting instead of f-strings. This avoids string interpolation when the log level is not active:

```python
# DO: Use % formatting (lazy evaluation)
logger.info("Processing %s users for tenant %s", count, tenant_id)
logger.debug("API response: %s", response_data)
logger.warning("Rate limited, retrying in %s seconds", retry_delay)

# DON'T: Use f-strings (eager evaluation)
logger.info(f"Processing {count} users for tenant {tenant_id}")
logger.debug(f"API response: {response_data}")
```

## Final Checklist

Before submitting your module:

- [ ] **Configuration**: CLI args, config validation, credential handling
- [ ] **Sync Pattern**: get() -> transform() -> load() -> cleanup()
- [ ] **Data Model**: Node properties, relationships, proper typing
- [ ] **Schema Fields**: Only use standard fields in `CartographyRelSchema`/`CartographyNodeSchema` subclasses
- [ ] **Scoped Cleanup**: Verify `scoped_cleanup=True` (default) for tenant-scoped resources
- [ ] **Error Handling**: Specific exceptions, required vs optional fields
- [ ] **Testing**: Integration tests for sync functions
- [ ] **Documentation**: Schema docs, docstrings, inline comments
- [ ] **Cleanup**: Proper cleanup job implementation
- [ ] **Indexing**: Extra indexes on frequently queried fields
- [ ] **Analysis Jobs** (optional): If your module needs post-ingestion enrichment, see [Analysis Jobs](analysis-jobs.md)
