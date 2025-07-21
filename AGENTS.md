# AGENTS.md: Cartography Intel Module Development Guide

> **For AI Coding Assistants**: This document provides comprehensive guidance for understanding and developing Cartography intel modules. It contains codebase-specific patterns, architectural decisions, and implementation details necessary for effective AI-assisted development within the Cartography project.

This guide teaches you how to write intel modules for Cartography using the modern data model approach. We'll walk through real examples from the codebase to show you the patterns and best practices.

## 🤖 AI Assistant Quick Reference

**Key Cartography Concepts:**
- **Intel Module**: Component that fetches data from external APIs and loads into Neo4j
- **Sync Pattern**: `get()` → `transform()` → `load()` → `cleanup()`
- **Data Model**: Declarative schema using `CartographyNodeSchema` and `CartographyRelSchema`
- **Update Tag**: Timestamp used for cleanup jobs to remove stale data

**Critical Files to Know:**
- `cartography/config.py` - Configuration object definitions
- `cartography/cli.py` - Command-line argument definitions
- `cartography/client/core/tx.py` - Core `load()` function
- `cartography/graph/job.py` - Cleanup job utilities
- `cartography/models/core/` - Base data model classes

## 📋 Table of Contents

1. @Quick Start: Copy an Existing Module
2. @Module Structure Overview
3. @The Sync Pattern: Get, Transform, Load, Cleanup
4. @Data Model: Defining Nodes and Relationships
5. @Advanced Node Schema Properties
6. @One-to-Many Relationships
7. @Configuration and Credentials
8. @Error Handling
9. @Testing Your Module
10. @Common Patterns and Examples
11. @Troubleshooting Guide
12. @Quick Reference

## 🚀 Quick Start: Copy an Existing Module {#quick-start}

The fastest way to get started is to copy the structure from an existing module:

- **Simple module**: `cartography/intel/lastpass/` - Basic user sync with API calls
- **Complex module**: `cartography/intel/aws/ec2/instances.py` - Multiple relationships and data types
- **Reference documentation**: `docs/root/dev/writing-intel-modules.md`

## 🏗️ Module Structure Overview {#module-structure}

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

## 🔄 The Sync Pattern: Get, Transform, Load, Cleanup {#sync-pattern}

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
    Sync function following the standard pattern
    """
    # 1. GET - Fetch data from API
    raw_data = get(api_key, tenant_id)

    # 2. TRANSFORM - Shape data for ingestion
    transformed_data = transform(raw_data)

    # 3. LOAD - Ingest to Neo4j using data model
    load_users(neo4j_session, transformed_data, tenant_id, update_tag)

    # 4. CLEANUP - Remove stale data
    cleanup(neo4j_session, common_job_parameters)
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
   # ❌ DON'T: Add complex error handling in get()
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

   # ✅ DO: Keep it simple and let errors propagate
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
   # ❌ DON'T: Silently continue on error
   def get_data() -> dict[str, Any]:
       try:
           return api.get_data()
       except Exception:
           return {}  # Silently continue with empty data

   # ✅ DO: Let errors propagate
   def get_data() -> dict[str, Any]:
       return api.get_data()  # Let errors propagate to caller
   ```

4. **Timeout Configuration**: Set appropriate timeouts to avoid hanging:
   ```python
   # ✅ DO: Set timeouts
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

            # Convert timestamps if needed
            "created_at": (
                int(dt_parse.parse(user_data["created_at"]).timestamp() * 1000)
                if user_data.get("created_at") else None
            ),
        }
        result.append(transformed_user)

    return result
```

**Key Principles:**
- **Required fields**: Use `data["field"]` - let it fail if missing
- **Optional fields**: Use `data.get("field")` - defaults to `None`
- **Consistency**: Use `None` for missing values, not empty strings

## 📊 Data Model: Defining Nodes and Relationships {#data-model}

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
- First parameter: Key in your data dict or kwarg name
- `extra_index=True`: Create database index for better query performance
- `set_in_kwargs=True`: Value comes from kwargs passed to `load()`, not from individual records

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

**✅ Correct Examples:**
- **AWS Resources**: Point to `AWSAccount` (tenant = AWS account)
- **Azure Resources**: Point to `AzureSubscription` (tenant = Azure subscription)
- **GCP Resources**: Point to `GCPProject` (tenant = GCP project)
- **SaaS Applications**: Point to `YourServiceTenant` (tenant = organization/company)
- **GitHub Resources**: Point to `GitHubOrganization` (tenant = GitHub org)

**❌ Incorrect Examples:**
- Pointing to a parent resource that's not tenant-like (e.g., `ECSTaskDefinition` → `ECSTask`)
- Pointing to infrastructure components (e.g., `ECSContainer` → `ECSTask`)
- Pointing to logical groupings that aren't organizational boundaries

**Example: AWS ECS Container Definitions**

```python
# ✅ CORRECT: Container definitions belong to AWS accounts
@dataclass(frozen=True)
class ECSContainerDefinitionSchema(CartographyNodeSchema):
    label: str = "ECSContainerDefinition"
    properties: ECSContainerDefinitionNodeProperties = ECSContainerDefinitionNodeProperties()
    sub_resource_relationship: ECSContainerDefinitionToAWSAccountRel = ECSContainerDefinitionToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([
        ECSContainerDefinitionToTaskDefinitionRel(),  # Business relationship
    ])

# ✅ CORRECT: Relationship to AWS Account (tenant-like)
@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("AWS_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerDefinitionToAWSAccountRelProperties = ECSContainerDefinitionToAWSAccountRelProperties()

# ✅ CORRECT: Business relationship to task definition (not tenant-like)
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
    direction: LinkDirection = LinkDirection.OUTWARD            # Direction of relationship
    rel_label: str = "RESOURCE"                                 # Relationship label
    properties: YourServiceTenantToUserRelProperties = YourServiceTenantToUserRelProperties()
```

**Relationship Directions:**
- `LinkDirection.OUTWARD`: `(:YourServiceUser)-[:RESOURCE]->(:YourServiceTenant)`
- `LinkDirection.INWARD`: `(:YourServiceUser)<-[:RESOURCE]-(:YourServiceTenant)`

### Advanced Node Schema Properties

#### Extra Node Labels

Add additional Neo4j labels to your nodes using `extra_node_labels`:

```python
from cartography.models.core.nodes import ExtraNodeLabels

@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()

    # Add extra labels like "Identity" and "Asset" to the node
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Identity", "Asset"])
```

This creates nodes with multiple labels: `(:YourServiceUser:Identity:Asset)`.

#### Scoped Cleanup

Control cleanup behavior with `scoped_cleanup`:

```python
@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()

    # Default behavior (scoped_cleanup=True): Only clean up users within the current tenant
    # scoped_cleanup: bool = True  # This is the default, no need to specify
```

**⚠️ When to Override `scoped_cleanup`:**

Set `scoped_cleanup=False` **ONLY** for intel modules that don't have a clear tenant-like entity:

```python
@dataclass(frozen=True)
class VulnerabilitySchema(CartographyNodeSchema):
    label: str = "Vulnerability"
    properties: VulnerabilityNodeProperties = VulnerabilityNodeProperties()
    sub_resource_relationship: None = None  # No tenant relationship

    # Vulnerabilities are global data, not scoped to a specific tenant
    scoped_cleanup: bool = False
```

**Examples where `scoped_cleanup=False` makes sense:**
- Vulnerability databases (CVE data is global)
- Threat intelligence feeds (IOCs are not tenant-specific)
- Public certificate transparency logs
- Global DNS/domain information

**Default behavior (`scoped_cleanup=True`) is correct for:**
- User accounts (scoped to organization/tenant)
- Infrastructure resources (scoped to AWS account, Azure subscription, etc.)
- Application assets (scoped to company/tenant)

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

## 🔗 One-to-Many Relationships {#one-to-many}

Sometimes you need to connect one node to many others. Example from AWS route tables:

### Source Data
```python
# Route table with multiple subnet associations
{
    "RouteTableId": "rtb-123",
    "Associations": [
        {"SubnetId": "subnet-abc"},
        {"SubnetId": "subnet-def"},
    ]
}
```

### Transform for One-to-Many
```python
def transform_route_tables(route_tables):
    result = []
    for rt in route_tables:
        transformed = {
            "id": rt["RouteTableId"],
            # Extract list of subnet IDs
            "subnet_ids": [assoc["SubnetId"] for assoc in rt.get("Associations", []) if "SubnetId" in assoc],
        }
        result.append(transformed)
    return result
```

### Define One-to-Many Relationship
```python
@dataclass(frozen=True)
class RouteTableToSubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "subnet_id": PropertyRef("subnet_ids", one_to_many=True),  # KEY: one_to_many=True
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: RouteTableToSubnetRelProperties = RouteTableToSubnetRelProperties()
```

**The Magic**: `one_to_many=True` tells Cartography to create a relationship to each subnet whose `subnet_id` is in the `subnet_ids` list.

### ⚠️ Common Schema Mistakes to Avoid

**DO NOT add custom properties to `CartographyRelSchema` or `CartographyNodeSchema` subclasses**: These dataclasses are processed by Cartography's core loading system, which only recognizes the standard fields defined in the base classes. Any additional fields you add will be ignored and have no effect.

```python
# ❌ Don't do this - custom fields are ignored by the loading system
@dataclass(frozen=True)
class MyRelationship(CartographyRelSchema):
    target_node_label: str = "SomeNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("some_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()
    # ❌ These custom fields do nothing:
    conditional_match_property: str = "some_id"
    custom_flag: bool = True
    extra_config: dict = {"key": "value"}

# ❌ Don't do this either - custom fields on node schemas are also ignored
@dataclass(frozen=True)
class MyNodeSchema(CartographyNodeSchema):
    label: str = "MyNode"
    properties: MyNodeProperties = MyNodeProperties()
    sub_resource_relationship: MyRel = MyRel()
    # ❌ This custom field does nothing:
    custom_setting: str = "ignored"

# ✅ Do this instead - stick to the standard schema fields only
@dataclass(frozen=True)
class MyRelationship(CartographyRelSchema):
    target_node_label: str = "SomeNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("some_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()

@dataclass(frozen=True)
class MyNodeSchema(CartographyNodeSchema):
    label: str = "MyNode"
    properties: MyNodeProperties = MyNodeProperties()
    sub_resource_relationship: MyRel = MyRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["AnotherLabel", ...]) # Optional
    other_relationships: OtherRelationships = OtherRelationships([...])  # Optional
    scoped_cleanup: bool = True  # Optional, defaults to True, almost should never be overridden. This is only used for intel modules that don't have a clear tenant-like entity.
```

**Standard fields for `CartographyRelSchema`:**
- `target_node_label`: str
- `target_node_matcher`: TargetNodeMatcher
- `direction`: LinkDirection
- `rel_label`: str
- `properties`: CartographyRelProperties subclass

**Standard fields for `CartographyNodeSchema`:**
- `label`: str
- `properties`: CartographyNodeProperties subclass
- `sub_resource_relationship`: CartographyRelSchema subclass
- `other_relationships`: OtherRelationships (optional)
- `extra_node_labels`: ExtraNodeLabels (optional)
- `scoped_cleanup`: bool (optional, defaults to True, almost should never be overridden. This is only used for intel modules that don't have a clear tenant-like entity.)

If you need conditional behavior, handle it in your transform function by setting field values to `None` when relationships shouldn't be created, or by filtering your data before calling `load()`.

## ⚙️ Configuration and Credentials {#configuration}

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

## 🚨 Error Handling {#error-handling}

Follow these principles for robust error handling:

### DO: Catch Specific Exceptions
```python
import requests


def get_users(api_key: str) -> dict[str, Any]:
    try:
        response = requests.get(f"https://api.service.com/users", headers={"Authorization": f"Bearer {api_key}"})
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
```

### DON'T: Catch Base Exception
```python
# ❌ Don't do this - makes debugging impossible
try:
    risky_operation()
except Exception:
    logger.error("Something went wrong")
    pass  # Silently continue - BAD!
```

### Required vs Optional Field Access

```python
def transform_user(user_data: dict[str, Any]) -> dict[str, Any]:
    return {
        # ✅ Required field - let it raise KeyError if missing
        "id": user_data["id"],
        "email": user_data["email"],

        # ✅ Optional field - gracefully handle missing data
        "name": user_data.get("display_name"),
        "phone": user_data.get("phone_number"),

        # ✅ Neo4j handles datetime objects natively - no need for manual parsing
        "last_login": user_data.get("last_login"),  # AWS/API returns ISO 8601 dates
    }
```

### Date Handling

Neo4j 4+ supports native Python datetime objects and ISO 8601 formatted strings. Avoid manual datetime parsing:

```python
# ❌ DON'T: Manually parse dates or convert to epoch timestamps
"created_at": int(dt_parse.parse(user_data["created_at"]).timestamp() * 1000)
"last_login": dict_date_to_epoch({"d": dt_parse.parse(data["last_login"])}, "d")

# ✅ DO: Pass datetime values directly
"created_at": user_data.get("created_at")  # AWS/API returns ISO 8601 dates
"last_login": user_data.get("last_login")  # Neo4j handles these natively
```

## 🧪 Testing Your Module {#testing}

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

### Unit Tests

(Optional) Test your transform functions in `tests/unit/cartography/intel/your_service/`:

```python
# tests/unit/cartography/intel/your_service/test_users.py
from cartography.intel.your_service.users import transform
from tests.data.your_service.users import MOCK_USERS_RESPONSE


def test_transform_users():
    result = transform(MOCK_USERS_RESPONSE)

    assert len(result) == 2

    alice = result[0]
    assert alice["id"] == "user-123"
    assert alice["email"] == "alice@example.com"
    assert alice["name"] == "Alice Smith"
    assert alice["is_admin"] is False
    assert alice["last_login"] is not None  # Converted timestamp

    bob = result[1]
    assert bob["id"] == "user-456"
    assert bob["last_login"] is None  # Handled missing data
```

### Integration Tests

Test actual Neo4j loading in `tests/integration/cartography/intel/your_service/`:

**Key Principle: Test outcomes, not implementation details.**

Focus on verifying that data is written to the graph as expected, rather than testing internal function parameters or implementation details. Mock external dependencies (APIs, databases) when necessary, but avoid brittle parameter testing.

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

    # ✅ DO: Test outcomes - verify data is written to the graph as expected
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

    # ✅ DO: Mock external dependencies when needed
    # mock_api.return_value = MOCK_USERS_RESPONSE  # Good - provides test data
    # (Prefer the decorator style though)

    # ❌ DON'T: Test brittle implementation details
    # mock_api.assert_called_once_with("fake-api-key", TEST_TENANT_ID)  # Brittle!
    # mock_api.assert_called_with(specific_params)  # Brittle!
```

**What to Test:**
- ✅ **Outcomes**: Nodes created with correct properties
- ✅ **Outcomes**: Relationships created between expected nodes

**What NOT to Test:**
- ❌ **Implementation**: Function parameters passed to mocks (brittle!)
- ❌ **Implementation**: Internal function call order
- ❌ **Implementation**: Mock call counts unless absolutely necessary

**When to Mock:**
- ✅ External APIs (AWS, Azure, third-party services) - provide test data
- ✅ Database connections - avoid real connections
- ✅ Network calls - avoid real network requests

**When NOT to Mock:**
- ❌ Internal Cartography functions
- ❌ Data transformation logic
- ❌ The function that is being tested

## 📚 Common Patterns and Examples {#common-patterns}

### Pattern 1: Simple Service with Users (LastPass Style)

Perfect for SaaS services with user management:

```python
# Data flow
API Response → transform() → [{"id": "123", "email": "user@example.com", ...}] → load()

# Key characteristics:
- One main entity type (users)
- Simple tenant relationship
- Standard fields (id, email, created_at, etc.)
```

### Pattern 2: Complex Infrastructure (AWS EC2 Style)

For infrastructure with multiple related resources:

```python
# Data flow
API Response → transform() → Multiple lists → Multiple load() calls

# Key characteristics:
- Multiple entity types (instances, security groups, subnets)
- Complex relationships between entities
- Regional/account-scoped resources
```

### Pattern 3: Hierarchical Resources (Route Tables Style)

For resources that contain lists of related items:

```python
# One-to-many transformation
{
    "RouteTableId": "rtb-123",
    "Associations": [{"SubnetId": "subnet-abc"}, {"SubnetId": "subnet-def"}]
}
↓
{
    "id": "rtb-123",
    "subnet_ids": ["subnet-abc", "subnet-def"]  # Flattened for one_to_many
}
```

### Cleanup Jobs

Always implement cleanup to remove stale data:

```python
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    """
    Remove nodes that weren't updated in this sync run
    """
    logger.debug("Running Your Service cleanup job")

    # Cleanup users
    GraphJob.from_node_schema(YourServiceUserSchema(), common_job_parameters).run(neo4j_session)
```

### Schema Documentation

Always document your schema in `docs/schema/your_service.md`:

```markdown
## Your Service Schema

### YourServiceUser

Represents a user in Your Service.

| Field | Description |
|-------|-------------|
| id | Unique user identifier |
| email | User email address |
| name | User display name |
| created_at | Account creation timestamp |
| last_login | Last login timestamp |
| is_admin | Admin privileges flag |

#### Relationships

- User belongs to tenant: `(:YourServiceUser)-[:RESOURCE]->(:YourServiceTenant)`
- User connected to human: `(:YourServiceUser)<-[:IDENTITY_YOUR_SERVICE]-(:Human)`
```

### Multiple Intel Modules Modifying the Same Node Type

It is possible (and encouraged) for more than one intel module to modify the same node type. However, there are two distinct patterns for this:

**Simple Relationship Pattern**: When data type A only refers to data type B by an ID without providing additional properties about B, we can just define a relationship schema. This way when A is loaded, the relationship schema performs a `MATCH` to find and connect to existing nodes of type B.

For example, when an RDS instance refers to EC2 security groups by ID, we create a relationship from the RDS instance to the security group nodes, since the RDS API doesn't provide additional properties about the security groups beyond their IDs.

```python
# RDS Instance refers to Security Groups by ID only
@dataclass(frozen=True)
class RDSInstanceToSecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("SecurityGroupId"),  # Just the ID, no additional properties
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: RDSInstanceToSecurityGroupRelProperties = RDSInstanceToSecurityGroupRelProperties()
```

**Composite Node Pattern**: When a data type A refers to another data type B and offers additional fields about B that B doesn't have itself, we should define a composite node schema. This composite node would be named "`BASchema`" to denote that it's a "`B`" object as known by an "`A`" object. When loaded, the composite node schema targets the same node label as the primary `B` schema, allowing the loading system to perform a `MERGE` operation that combines properties from both sources.

For example, in the AWS EC2 module, we have both `EBSVolumeSchema` (from the EBS API) and `EBSVolumeInstanceSchema` (from the EC2 Instance API). The EC2 Instance API provides additional properties about EBS volumes that the EBS API doesn't have, such as `deleteontermination`. Both schemas target the same `EBSVolume` node label, allowing the node to accumulate properties from both sources.

```python
# EC2 Instance provides additional properties about EBS Volumes
@dataclass(frozen=True)
class EBSVolumeInstanceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("VolumeId")
    arn: PropertyRef = PropertyRef("Arn", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Additional property that EBS API doesn't have
    deleteontermination: PropertyRef = PropertyRef("DeleteOnTermination")

@dataclass(frozen=True)
class EBSVolumeInstanceSchema(CartographyNodeSchema):
    label: str = "EBSVolume"  # Same label as EBSVolumeSchema
    properties: EBSVolumeInstanceProperties = EBSVolumeInstanceProperties()
    sub_resource_relationship: EBSVolumeToAWSAccountRel = EBSVolumeToAWSAccountRel()
    # ... other relationships
```

The key distinction is whether the referring module provides additional properties about the target entity. If it does, use a composite node schema. If it only provides IDs, use a simple relationship schema.

## 🎯 Final Checklist

Before submitting your module:

- [ ] ✅ **Configuration**: CLI args, config validation, credential handling
- [ ] ✅ **Sync Pattern**: get() → transform() → load() → cleanup()
- [ ] ✅ **Data Model**: Node properties, relationships, proper typing
- [ ] ✅ **Schema Fields**: Only use standard fields in `CartographyRelSchema`/`CartographyNodeSchema` subclasses
- [ ] ✅ **Scoped Cleanup**: Verify `scoped_cleanup=True` (default) for tenant-scoped resources, `False` only for global data
- [ ] ✅ **Error Handling**: Specific exceptions, required vs optional fields
- [ ] ✅ **Testing**: Unit tests for transform, integration tests for loading
- [ ] ✅ **Documentation**: Schema docs, docstrings, inline comments
- [ ] ✅ **Cleanup**: Proper cleanup job implementation
- [ ] ✅ **Indexing**: Extra indexes on frequently queried fields

Remember: Start simple, iterate, and use existing modules as references. The Cartography community is here to help! 🚀

## 🔧 Troubleshooting Guide {#troubleshooting}

### Common Issues and Solutions

#### Import Errors
```python
# ❌ Problem: ModuleNotFoundError for your new module
# ✅ Solution: Ensure __init__.py files exist in all directories
cartography/intel/your_service/__init__.py
cartography/models/your_service/__init__.py
```

#### Schema Validation Errors
```python
# ❌ Problem: "PropertyRef validation failed"
# ✅ Solution: Check dataclass syntax and PropertyRef definitions
@dataclass(frozen=True)  # Don't forget frozen=True!
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")  # Must have type annotation
```

#### Relationship Connection Issues
```python
# ❌ Problem: Relationships not created
# ✅ Solution: Ensure target nodes exist before creating relationships
# Load parent nodes first:
load(neo4j_session, TenantSchema(), tenant_data, lastupdated=update_tag)
# Then load child nodes with relationships:
load(neo4j_session, UserSchema(), user_data, lastupdated=update_tag, TENANT_ID=tenant_id)
```

#### Cleanup Job Failures
```python
# ❌ Problem: "GraphJob failed" during cleanup
# ✅ Solution: Check common_job_parameters structure
common_job_parameters = {
    "UPDATE_TAG": config.update_tag,  # Must match what's set on nodes
    "TENANT_ID": tenant_id,           # If using scoped cleanup (default)
}

# ❌ Problem: Cleanup deleting too much data (wrong scoped_cleanup setting)
# ✅ Solution: Verify scoped_cleanup setting is appropriate
@dataclass(frozen=True)
class MySchema(CartographyNodeSchema):
    # For tenant-scoped resources (default, most common):
    # scoped_cleanup: bool = True  # Default - no need to specify

    # For global resources only (rare):
    scoped_cleanup: bool = False  # Only for vuln data, threat intel, etc.
```

#### Data Transform Issues
```python
# ❌ Problem: KeyError during transform
# ✅ Solution: Handle required vs optional fields correctly
{
    "id": data["id"],                    # Required - let it fail
    "name": data.get("name"),            # Optional - use .get()
    "email": data.get("email", ""),      # ❌ Don't use empty string default
    "email": data.get("email"),          # ✅ Use None default
}
```

#### Schema Definition Issues
```python
# ❌ Problem: Adding custom fields to schema classes
# ✅ Solution: Remove them - only standard fields are recognized by the loading system
@dataclass(frozen=True)
class MyRel(CartographyRelSchema):
    # Remove any custom fields like these:
    # conditional_match_property: str = "some_field"  # ❌ Ignored
    # custom_flag: bool = True                        # ❌ Ignored
    # extra_config: dict = {}                         # ❌ Ignored

    # Keep only the standard relationship fields
    target_node_label: str = "TargetNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(...)
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()
```

#### Performance Issues
```python
# ❌ Problem: Slow queries
# ✅ Solution: Add indexes to frequently queried fields
email: PropertyRef = PropertyRef("email", extra_index=True)

# ✅ Query on indexed fields only
MATCH (u:User {id: $user_id})  # Good - id is always indexed
MATCH (u:User {name: $name})   # Bad - name might not be indexed

Note though that if a field is referred to in a target node matcher, it will be indexed automatically.
```

### Debugging Tips for AI Assistants

1. **Check existing patterns first**: Look at similar modules in `cartography/intel/` before creating new patterns
2. **Verify data model imports**: Ensure all `CartographyNodeSchema` imports are correct
3. **Test transform functions**: Always test data transformation logic with real API responses
4. **Validate Neo4j queries**: Use Neo4j browser to test queries manually if relationships aren't working
5. **Check file naming**: Module files should match the service name (e.g., `cartography/intel/lastpass/users.py`)

### Key Files for Debugging

- **Logs**: Look for import errors in application logs
- **Tests**: Check `tests/integration/cartography/intel/` for similar patterns
- **Models**: Review `cartography/models/` for existing relationship patterns
- **Core**: Understand `cartography/client/core/tx.py` for load function behavior

## 📝 Quick Reference Cheat Sheet {#quick-reference-cheat-sheet}

### Type Hints Style Guide

Use Python 3.9+ style type hints throughout your code:

```python
# ✅ DO: Use built-in type hints (Python 3.9+)
def get_users(api_key: str) -> dict[str, Any]:
    ...

def transform(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ...

# ❌ DON'T: Use objects from typing module
def get_users(api_key: str) -> Dict[str, Any]:
    ...

def transform(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ...

# ✅ DO: Use union operator for optional types
def process_user(user_id: str | None) -> None:
    ...

# ❌ DON'T: Use Optional from typing
def process_user(user_id: Optional[str]) -> None:
    ...
```

### Essential Imports
```python
# Core data model
from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import (
    CartographyRelProperties, CartographyRelSchema, LinkDirection,
    make_target_node_matcher, TargetNodeMatcher, OtherRelationships
)

# Loading and cleanup
from cartography.client.core.tx import load
from cartography.graph.job import GraphJob

# Utilities
from cartography.util import timeit
from cartography.config import Config
```

### Required Node Properties
```python
@dataclass(frozen=True)
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")                                    # REQUIRED: Unique identifier
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)  # REQUIRED: Auto-managed
    # Your business properties here...
```

### Standard Sync Function Template
```python
@timeit
def sync(neo4j_session: neo4j.Session, api_key: str, tenant_id: str,
         update_tag: int, common_job_parameters: dict[str, Any]) -> None:
    data = get(api_key, tenant_id)              # 1. GET
    transformed = transform(data)               # 2. TRANSFORM
    load_entities(neo4j_session, transformed,   # 3. LOAD
                 tenant_id, update_tag)
    cleanup(neo4j_session, common_job_parameters)  # 4. CLEANUP
```

### Standard Load Pattern
```python
def load_entities(neo4j_session: neo4j.Session, data: list[dict],
                 tenant_id: str, update_tag: int) -> None:
    load(neo4j_session, YourSchema(), data,
         lastupdated=update_tag, TENANT_ID=tenant_id)
```

### Standard Cleanup Pattern
```python
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    GraphJob.from_node_schema(YourSchema(), common_job_parameters).run(neo4j_session)
```

### Relationship Direction Quick Reference
```python
# OUTWARD: (:Source)-[:REL]->(:Target)
direction: LinkDirection = LinkDirection.OUTWARD

# INWARD: (:Source)<-[:REL]-(:Target)
direction: LinkDirection = LinkDirection.INWARD
```

### One-to-Many Relationship Pattern
```python
# Transform: Create list field
{"entity_id": "123", "related_ids": ["a", "b", "c"]}

# Schema: Use one_to_many=True
target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
    "id": PropertyRef("related_ids", one_to_many=True),
})
```

### Configuration Validation Template
```python
def start_ingestion(neo4j_session: neo4j.Session, config: Config) -> None:
    if not config.your_api_key_env_var:
        logger.info("Module not configured - skipping")
        return

    api_key = os.getenv(config.your_api_key_env_var)
    if not api_key:
        logger.error(f"Environment variable {config.your_api_key_env_var} not set")
        return
```

### File Structure Template
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
