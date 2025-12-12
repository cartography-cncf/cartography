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
7. @MatchLinks: Connecting Existing Nodes
8. @Ontology Integration: Mapping Users and Devices
9. @Creating Security Rules with Ontology
10. @Configuration and Credentials
11. @Error Handling
12. @Testing Your Module
13. @Refactoring Legacy Code to Data Model
14. @Common Patterns and Examples
15. @Troubleshooting Guide
16. @Quick Reference

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
- First parameter: Key in your data dict or kwarg name. Use keys when you are ingesting a list of records. Use kwargs when you want to set the same value for all records in the list of records.
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

## 🔗 MatchLinks: Connecting Existing Nodes {#matchlinks}

**⚠️ IMPORTANT: Use MatchLinks sparingly due to performance impact!**

MatchLinks are a specialized tool for creating relationships between existing nodes in the graph. They should be used **only** in these two specific scenarios:

### Scenario 1: Connecting Two Existing Node Types

When you need to connect two different types of nodes that already exist in the graph, and the relationship data comes from a separate API call or data source.

**Example**: AWS Identity Center role assignments connecting users to roles:

```python
# Data from a separate API call that maps users to roles
role_assignments = [
    {
        "UserId": "user-123",
        "RoleArn": "arn:aws:iam::123456789012:role/AdminRole",
        "AccountId": "123456789012",
    },
    {
        "UserId": "user-456",
        "RoleArn": "arn:aws:iam::123456789012:role/ReadOnlyRole",
        "AccountId": "123456789012",
    }
]

# MatchLink schema to connect existing AWSSSOUser nodes to existing AWSRole nodes
@dataclass(frozen=True)
class RoleAssignmentAllowedByMatchLink(CartographyRelSchema):
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "arn": PropertyRef("RoleArn"),
    })
    source_node_label: str = "AWSSSOUser"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher({
        "id": PropertyRef("UserId"),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_BY"
    properties: RoleAssignmentRelProperties = RoleAssignmentRelProperties()

# Load the relationships
load_matchlinks(
    neo4j_session,
    RoleAssignmentAllowedByMatchLink(),
    role_assignments,
    lastupdated=update_tag,
    _sub_resource_label="AWSAccount",
    _sub_resource_id=aws_account_id,
)
```

### Scenario 2: Rich Relationship Properties

When you need to store detailed metadata on relationships that doesn't make sense as separate nodes.

**Example**: AWS Inspector findings connecting to packages with remediation details:

```python
# Data with rich relationship properties
finding_to_package_data = [
    {
        "findingarn": "arn:aws:inspector2:us-east-1:123456789012:finding/abc123",
        "packageid": "openssl|0:1.1.1k-1.el8.x86_64",
        "filePath": "/usr/lib64/libssl.so.1.1",
        "fixedInVersion": "0:1.1.1l-1.el8",
        "remediation": "Update OpenSSL to version 1.1.1l or later",
    }
]

# MatchLink schema with rich properties
@dataclass(frozen=True)
class InspectorFindingToPackageMatchLink(CartographyRelSchema):
    target_node_label: str = "AWSInspectorPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("packageid"),
    })
    source_node_label: str = "AWSInspectorFinding"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher({
        "id": PropertyRef("findingarn"),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_VULNERABLE_PACKAGE"
    properties: InspectorFindingToPackageRelProperties = InspectorFindingToPackageRelProperties()

@dataclass(frozen=True)
class InspectorFindingToPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Rich relationship properties
    filepath: PropertyRef = PropertyRef("filePath")
    fixedinversion: PropertyRef = PropertyRef("fixedInVersion")
    remediation: PropertyRef = PropertyRef("remediation")
```

### ⚠️ Performance Impact

MatchLinks have significant performance overhead because they require:

1. **API Call A** → Write Node A to graph
2. **API Call B** → Write Node B to graph
3. **Read Node A** from graph
4. **Read Node B** from graph
5. **Write relationship** between A and B to graph

**Prefer standard node schemas + relationship schemas** whenever possible:

```python
# ✅ DO: Use standard node schema with relationships
@dataclass(frozen=True)
class YourNodeSchema(CartographyNodeSchema):
    label: str = "YourNode"
    properties: YourNodeProperties = YourNodeProperties()
    sub_resource_relationship: YourNodeToTenantRel = YourNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships([
        YourNodeToOtherNodeRel(),  # Standard relationship
    ])

# ❌ DON'T: Use MatchLinks unless absolutely necessary
# Only use when you can't define the relationship in the node schema
```

### When NOT to Use MatchLinks

**❌ Don't use MatchLinks for:**
- Standard parent-child relationships (use `other_relationships` in node schema)
- Simple one-to-many relationships (use `one_to_many=True` in standard relationships)
- When you can define the relationship in the node schema
- Performance-critical scenarios

**✅ Use MatchLinks only for:**
- Connecting two existing node types from separate data sources
- Relationships with rich metadata that doesn't belong in nodes

### Required MatchLink Properties

All MatchLink relationship properties must include these mandatory fields:

```python
@dataclass(frozen=True)
class YourMatchLinkRelProperties(CartographyRelProperties):
    # Required for all MatchLinks
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)

    # Your custom properties here
    custom_property: PropertyRef = PropertyRef("custom_property")
```

### MatchLink Cleanup

Always implement cleanup for MatchLinks:

```python
def cleanup(neo4j_session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    # Standard node cleanup
    GraphJob.from_node_schema(YourNodeSchema(), common_job_parameters).run(neo4j_session)

    # MatchLink cleanup
    GraphJob.from_matchlink(
        YourMatchLinkSchema(),
        "AWSAccount",  # _sub_resource_label
        common_job_parameters["AWS_ID"],  # _sub_resource_id
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
```

## 🌐 Ontology Integration: Mapping Users and Devices {#ontology-integration}

Cartography includes an **Ontology system** that provides both semantic labels and canonical nodes to unify data from multiple sources. This enables cross-module querying and provides a normalized view of identity and device management across your infrastructure.

### Overview of Ontology System

The Ontology system works in two ways:
1. **Semantic Labels**: Adds semantic labels (like `UserAccount`) and prefixed properties (`_ont_*`) directly to source nodes for cross-module querying during ingestion
2. **Canonical Nodes**: Creates canonical node (like `(:User:Ontology)`) that represent unified entities

### Types of Ontology Integration

**Semantic Labels (Recommended)**: Adds `UserAccount` labels and `_ont_*` properties to existing nodes:
- ✅ Simpler implementation - no additional node creation
- ✅ Direct querying of source nodes with normalized properties
- ✅ Automatic property mapping with special handling for data transformations
- ✅ Source tracking via `_ont_source` property

**Canonical Nodes (Legacy)**: Creates separate abstract `User`/`Device` nodes:
- ⚠️ More complex - requires separate node creation and relationship management
- ⚠️ Additional storage overhead
- ✅ Useful when you need to aggregate data from multiple sources into single entities

### Step 1: Add Ontology Mapping Configuration

Create mapping configurations in `cartography/models/ontology/mapping/data/`:

#### For Semantic Labels

```python
# cartography/models/ontology/mapping/data/useraccounts.py
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Add your mapping to the file
your_service_mapping = OntologyMapping(
    module_name="your_service",
    nodes=[
        OntologyNodeMapping(
            node_label="YourServiceUser",  # Your node label
            fields=[
                # Map your node fields to ontology fields with special handling
                OntologyFieldMapping(ontology_field="email", node_field="email"),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
                OntologyFieldMapping(ontology_field="fullname", node_field="display_name"),
                OntologyFieldMapping(ontology_field="firstname", node_field="first_name"),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
                # Special handling examples:
                OntologyFieldMapping(
                    ontology_field="inactive",
                    node_field="account_enabled",
                    special_handling="invert_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="has_mfa",
                    node_field="multifactor",
                    special_handling="to_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="inactive",
                    node_field="suspended",
                    special_handling="or_boolean",
                    extra={"fields": ["archived"]},
                ),
            ],
        ),
    ],
)
```

#### For Canonical Nodes

```python
# cartography/models/ontology/mapping/data/devices.py
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

# Add your mapping to the file
your_service_mapping = OntologyMapping(
    module_name="your_service",
    nodes=[
        OntologyNodeMapping(
            node_label="YourServiceDevice",  # Your node label
            fields=[
                # Map your node fields to ontology fields
                OntologyFieldMapping(ontology_field="hostname", node_field="device_name", required=True),  # Required field
                OntologyFieldMapping(ontology_field="os", node_field="operating_system"),
                OntologyFieldMapping(ontology_field="os_version", node_field="os_version"),
                OntologyFieldMapping(ontology_field="model", node_field="device_model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
                OntologyFieldMapping(ontology_field="serial_number", node_field="serial"),
            ],
        ),
    ],
    # Optional: Add relationship mappings to connect Users to Devices
    rels=[
        OntologyRelMapping(
            __comment__="Link Device to User based on YourServiceUser-YourServiceDevice ownership",
            query="""
                MATCH (u:User)-[:HAS_ACCOUNT]->(:YourServiceUser)-[:OWNS]->(:YourServiceDevice)<-[:OBSERVED_AS]-(d:Device)
                MERGE (u)-[r:OWNS]->(d)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $UPDATE_TAG
            """,
            interative=False,
        ),
    ],
)
```

### Step 2: Add Ontology Configuration to Your Node Schema

#### Semantic Labels
Simply add the semantic label - the ontology system will automatically add `_ont_*` properties at the ingestion time.

```python
from cartography.models.core.nodes import ExtraNodeLabels

@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    # Add UserAccount label for semantic ontology integration
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
```

That's it! The ontology system will automatically:
- Add `_ont_email`, `_ont_fullname`, etc. properties to your nodes
- Apply any special handling (boolean conversion, inversion, etc.)
- Add `_ont_source` property to track which module provided the data

#### Canonical Nodes

You need to define a Schema model for the canonical node and add a relationship to it (similar to regular intel nodes)

```python
@dataclass(frozen=True)
class UserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    fullname: PropertyRef = PropertyRef("fullname")
    firstname: PropertyRef = PropertyRef("firstname")
    lastname: PropertyRef = PropertyRef("lastname")
    inactive: PropertyRef = PropertyRef("inactive")


@dataclass(frozen=True)
class UserToUserAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:User)-[:HAS_ACCOUNT]->(:UserAccount)
# This is a relationship to a sementic label used by modules' users nodes
@dataclass(frozen=True)
class UserToUserAccountRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UserToUserAccountRelProperties = UserToUserAccountRelProperties()


@dataclass(frozen=True)
class UserSchema(CartographyNodeSchema):
    label: str = "User"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: UserNodeProperties = UserNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[UserToUserAccountRel()],
    )
```

### Step 3: Understanding Ontology Field Mappings

#### Required Fields

The `required` parameter in `OntologyFieldMapping` serves two critical purposes:

**1. Data Quality Control**: When `required=True`, source nodes that lack this field (i.e., the field is `None` or missing) will be completely excluded from ontology node creation. This ensures only complete, usable data creates ontology nodes.

**2. Primary Identifier Validation**: Fields used as primary identifiers **must** be marked as required to ensure ontology nodes can always be properly identified and matched across data sources.

```python
# ✅ DO: Mark primary identifiers as required
OntologyFieldMapping(ontology_field="email", node_field="email", required=True),        # Users
OntologyFieldMapping(ontology_field="hostname", node_field="device_name", required=True), # Devices

# ✅ DO: Mark optional fields as not required (default)
OntologyFieldMapping(ontology_field="firstname", node_field="first_name"),  # Optional field
```

**Example**: If a `DuoUser` node has no email address and email is marked as `required=True`, no corresponding `User` ontology node will be created for that record.

#### Node Eligibility

The `eligible_for_source` parameter in `OntologyNodeMapping` controls whether this node mapping can create new ontology nodes (default: `True`).

**When to set `eligible_for_source=False`:**
- Node type lacks sufficient data to create meaningful ontology nodes (e.g., no email for Users)
- Node serves only as a connection point to existing ontology nodes
- Required fields are not available or reliable enough for primary node creation

```python
# Example: AWS IAM users don't have email addresses (required for User ontology nodes)
OntologyNodeMapping(
    node_label="AWSUser",
    eligible_for_source=False,  # Cannot create new User ontology nodes
    fields=[
        OntologyFieldMapping(ontology_field="username", node_field="name")
    ],
),
```

In this example, AWS IAM users can be linked to existing User ontology nodes through relationships, but they cannot create new User nodes since they lack email addresses.

### Step 4: Handle Complex Relationships

For services that have user-device relationships, add relationship mappings:

```python
# In your device mapping
rels=[
    OntologyRelMapping(
        __comment__="Connect users to their devices",
        query="""
            MATCH (u:User)-[:HAS_ACCOUNT]->(:YourServiceUser)-[:OWNS]->(:YourServiceDevice)<-[:OBSERVED_AS]-(d:Device)
            MERGE (u)-[r:OWNS]->(d)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $UPDATE_TAG
        """,
        interative=False,
    ),
]
```

## 🔐 Creating Security Rules

Cartography includes a powerful rules system that allows you to write security queries to identify potential attack surfaces, security gaps, and compliance issues across your infrastructure. The ontology system makes it easy to write rules that work across multiple cloud providers and services.

### Rule Architecture

Rules use a simple two-level hierarchy:

```
Rule (e.g., "unmanaged-accounts")
  └─ Fact (e.g., "unmanaged-accounts-ontology")
```

- **Rule**: Represents a security issue or attack surface (e.g., "User accounts not linked to a user identity")
- **Fact**: Individual Cypher query that gathers evidence about your environment
- **Finding**: Pydantic model that defines the structure of results

### Creating Rules

Combine facts from multiple providers (or use ontology nodes) for comprehensive coverage:

```python
from cartography.rules.spec.model import Fact, Finding, Maturity, Module, Rule

# AWS-specific fact
_aws_public_databases = Fact(
    id="aws-rds-public",
    name="Publicly accessible AWS RDS instances",
    description="AWS RDS databases exposed to the internet",
    cypher_query="""
    MATCH (db:RDSInstance)
    WHERE db.publicly_accessible = true
    RETURN db.id AS id, db.db_instance_identifier AS name, db.region AS region
    """,
    cypher_visual_query="""
    MATCH (db:RDSInstance)
    WHERE db.publicly_accessible = true
    RETURN db
    """,
    module=Module.AWS,
    maturity=Maturity.STABLE,
)

# Azure-specific fact
_azure_public_databases = Fact(
    id="azure-sql-public",
    name="Publicly accessible Azure SQL databases",
    description="Azure SQL databases exposed to the internet",
    cypher_query="""
    MATCH (db:AzureSQLServer)
    WHERE db.public_network_access = 'Enabled'
    RETURN db.id AS id, db.name AS name, db.location AS region
    """,
    cypher_visual_query="""
    MATCH (db:AzureSQLServer)
    WHERE db.public_network_access = 'Enabled'
    RETURN db
    """,
    module=Module.AZURE,
    maturity=Maturity.EXPERIMENTAL,
)

# Output model
class DatabaseExposedOutput(Finding):
    id: str | None = None
    name: str | None = None
    region: str | None = None

# Unified rule
database_exposed = Rule(
    id="database-exposed",
    name="Publicly Accessible Databases",
    description="Detects databases exposed to the internet across cloud providers",
    output_model=DatabaseExposedOutput,
    tags=("infrastructure", "attack_surface", "database"),
    facts=(_aws_public_databases, _azure_public_databases),
    version="0.1.0",
)
```

### Output Models with Pydantic

Each Rule must define an output model extending `Finding`:

```python
from cartography.rules.spec.model import Finding

class MyRuleOutput(Finding):
    """Output model for my custom rule."""

    # Define fields that will be populated from cypher_query results
    id: str | None = None              # Resource identifier
    email: str | None = None           # User email
    region: str | None = None          # Cloud region
    public_access: bool | None = None  # Access level
```

**Key Points:**
- **Inherit from `Finding`**: Your model must extend the base class
- **Match Query Aliases**: Field names must match `cypher_query` aliases
- **Automatic Handling**: The `source` field is auto-populated with module name

### Fact Maturity Levels

Mark fact maturity to indicate production-readiness:

#### `EXPERIMENTAL`
- New facts, recently added
- May have bugs or performance issues
- Limited production testing
- Use for testing new detection capabilities

```python
maturity=Maturity.EXPERIMENTAL
```

#### `STABLE`
- Production-ready, well-tested
- Optimized queries, consistent results
- Use for production monitoring and compliance

```python
maturity=Maturity.STABLE
```

### Rule Versioning

Use semantic versioning for rules:

```python
version="0.1.0"  # Initial release
version="0.2.0"  # Added new facts (minor)
version="0.2.1"  # Bug fix (patch)
version="1.0.0"  # Production ready (major)
```

### Step-by-Step: Creating a New Rule

1. **Create rule file** in `cartography/rules/data/rules/my_rule.py`:

2. **Register rule** in `cartography/rules/data/rules/__init__.py`:

```python
from cartography.rules.data.rules.my_rule import my_rule

RULES = {
    # ... existing rules
    my_rule.id: my_rule,
}
```

3. **Test your rule**:

```bash
# List rule details
cartography-rules list my-rule

# Run the rule
cartography-rules run my-rule

# Run with JSON output
cartography-rules run my-rule --output json

# Exclude experimental facts
cartography-rules run my-rule --no-experimental
```

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

### Fail Loudly When Assumptions Break

Cartography (both the backend ingestion jobs and any frontend surfaces that consume their results)
likes to fail loudly so that broken assumptions bubble exceptions up to operators instead of being
papered over.

- When key assumptions your code relies upon stop being true, **stop execution immediately** and let
  the error propagate. Add context if needed, then re-raise, rather than swallowing or downgrading
  the exception.
- Lean toward propagating errors up to callers instead of logging a warning inside a `try`/`except`
  block and continuing. Every time we continue execution after an unexpected error we risk silently
  corrupting downstream data.
- If you're confident data should always exist, access it directly. Allow natural `KeyError`,
  `AttributeError`, or `IndexError` exceptions to signal corruption instead of building extra guard
  rails or default placeholders.
- Avoid using `hasattr()`/`getattr()` (or language equivalents) to probe for attributes that our
  schemas guarantee. These checks often hide real contract violations and make debugging harder.
- Never manufacture "safe" default return values for dictionary keys, tuple indices, or other
  required data. Emit the real exception so the upstream issue can be fixed.

To mitigate common pitfalls:

- **Harmful try/except blocks** → Only catch exceptions when you can remediate them meaningfully.
  Otherwise, let them bubble up and fail fast.
- **Redundant attribute guards** → Remove `hasattr()`/`getattr()` shims for required fields and rely
  on our strongly-defined schemas and tests to detect breakage.
- **Defaulting required data** → Do not set fallback values for required dictionary keys or sequence
  indices. Allow the error to surface so the caller can address it.

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

### Unit Tests

Unit tests are only for testing smaller functions and verifying that the outputs are as expected.

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

## 🔄 Refactoring Legacy Code to Data Model {#refactoring-legacy}

**IMPORTANT**: A critical task for AI agents is refactoring legacy Cartography code from handwritten Cypher queries to the modern data model approach. This section provides a step-by-step procedure to safely perform these refactors.

### Overview

Legacy Cartography modules use handwritten Cypher queries to create nodes and relationships. The modern approach uses declarative data models that automatically generate optimized queries. Refactoring improves maintainability, performance, and consistency.

### 🚨 Step 1: Prevent Regressions (CRITICAL)

**Before touching any code**, ensure you have comprehensive test coverage:

#### 1a. Identify the Sync Function
- Locate the main `sync_*()` function for the module (refer to [#sync-pattern](#sync-pattern))
- This is usually named like `sync_ec2_instances()`, `sync_users()`, etc.
- Example: `cartography.intel.aws.ec2.instances.sync()`

#### 1b. Ensure Integration Test Exists
- Check for integration tests in `tests/integration/cartography/intel/[module]/`
- The test MUST call the sync function directly (refer to [#testing](#testing))
- If no test exists, **CREATE IT FIRST** before any refactoring:

```python
# Example: tests/integration/cartography/intel/aws/ec2/test_instances.py
from unittest.mock import patch
import cartography.intel.aws.ec2.instances
from tests.data.aws.ec2.instances import MOCK_INSTANCES_DATA
from tests.integration.util import check_nodes, check_rels

TEST_UPDATE_TAG = 123456789
TEST_AWS_ACCOUNT_ID = "123456789012"

@patch.object(cartography.intel.aws.ec2.instances, "get", return_value=MOCK_INSTANCES_DATA)
def test_sync_ec2_instances(mock_get, neo4j_session):
    """Test that EC2 instances sync correctly"""
    # Act - Call the sync function
    cartography.intel.aws.ec2.instances.sync(
        neo4j_session,
        boto3_session=None,  # Mocked
        regions=["us-east-1"],
        current_aws_account_id=TEST_AWS_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_AWS_ACCOUNT_ID,
        },
    )

    # Assert - Check expected nodes exist
    expected_nodes = {
        ("i-1234567890abcdef0", "running"),
        ("i-0987654321fedcba0", "stopped"),
    }
    assert check_nodes(neo4j_session, "EC2Instance", ["id", "state"]) == expected_nodes
```

- **CRITICAL**: Run the test and ensure it passes before proceeding
- If the test doesn't exist or fails, fix it first - **no exceptions**

### 🔧 Step 2: Convert to Data Model

Now safely convert the legacy code to use the modern data model:

#### 2a. Create Data Model Schema Files
Create schema files in `cartography/models/[module]/`:

```python
# cartography/models/aws/ec2/instances.py
from dataclasses import dataclass
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties, CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema, LinkDirection, make_target_node_matcher

@dataclass(frozen=True)
class EC2InstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    instanceid: PropertyRef = PropertyRef("InstanceId")
    state: PropertyRef = PropertyRef("State")
    # ... other properties

@dataclass(frozen=True)
class EC2InstanceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("AWS_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EC2InstanceToAWSAccountRelProperties = EC2InstanceToAWSAccountRelProperties()

@dataclass(frozen=True)
class EC2InstanceSchema(CartographyNodeSchema):
    label: str = "EC2Instance"
    properties: EC2InstanceNodeProperties = EC2InstanceNodeProperties()
    sub_resource_relationship: EC2InstanceToAWSAccountRel = EC2InstanceToAWSAccountRel()
```

#### 2b. Replace load_* Functions
Replace handwritten Cypher in load functions with data model `load()` calls:

```python
# Before (legacy)
def load_ec2_instances(neo4j_session, data, region, current_aws_account_id, update_tag):
    ingest_instances = """
    UNWIND $instances_list as instance
    MERGE (i:EC2Instance{id: instance.id})
    ON CREATE SET i.firstseen = timestamp()
    SET i.instanceid = instance.InstanceId,
        i.state = instance.State,
        i.lastupdated = $update_tag
    WITH i
    MATCH (owner:AWSAccount{id: $aws_account_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(ingest_instances, instances_list=data, aws_account_id=current_aws_account_id, update_tag=update_tag)

# After (data model)
def load_ec2_instances(neo4j_session, data, region, current_aws_account_id, update_tag):
    load(
        neo4j_session,
        EC2InstanceSchema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
    )
```

#### 2c. Replace cleanup_* Functions
Replace handwritten cleanup with data model cleanup:

```python
# Before (legacy)
def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ec2_instances_cleanup.json', neo4j_session, common_job_parameters)

# After (data model)
def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(EC2InstanceSchema(), common_job_parameters).run(neo4j_session)
```

#### 2d. Test Continuously
- Run your integration test after each change
- Ensure it still passes - if not, debug before continuing
- You may need to update minor details in tests due to data model differences

### 🧹 Step 3: Cleanup Legacy Files

Once tests pass, clean up legacy infrastructure:

#### 3a. Remove Index Entries
Remove manual index entries from `cartography/data/indexes.cypher`:

```cypher
# Remove entries like these - data model creates indexes automatically
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.lastupdated);
```

**Note**: Only remove indexes for nodes you've converted to data model. Leave others untouched.

#### 3b. Remove Cleanup Job Files
Remove corresponding cleanup JSON files from `cartography/data/jobs/cleanup/`:

```bash
# Remove files like:
rm cartography/data/jobs/cleanup/aws_import_ec2_instances_cleanup.json
```

**Note**: Only remove cleanup files for modules you've fully converted.

### 🔍 Common Refactoring Patterns

#### Pattern 1: Simple Node Migration
Most legacy nodes can be directly converted to data model schemas.

#### Pattern 2: Complex Relationships
For modules with complex relationships, you may need:
- **One-to-Many relationships** (see [#one-to-many](#one-to-many))
- **Composite Node Pattern** for nodes that get data from multiple sources

#### Pattern 3: MatchLinks for Complex Cases
Use [MatchLinks](#matchlinks) sparingly, only when:
- Connecting two existing node types from separate data sources
- Rich relationship properties that don't belong in nodes

### ⚠️ Things You May Encounter

#### Multiple Intel Modules Modifying Same Nodes
When refactoring modules that modify the same node type:
- Use **Simple Relationship Pattern** if only referencing by ID
- Use **Composite Node Pattern** for different views of the same entity from different data sources (see [Common Patterns](#common-patterns))

#### Legacy Test Adjustments
Older tests may need small tweaks:
- Update expected property names if data model changes them
- Adjust relationship directions if needed
- Remove tests for manual cleanup jobs (data model handles this)

#### Complex Cypher Queries
Some legacy queries are complex. Break them down:
1. Identify what nodes/relationships are being created
2. Map to data model schemas
3. Use multiple `load()` calls if needed

### 🚫 What NOT to Test

**Do NOT explicitly test cleanup functions** unless there's a specific concern:
- Data model handles complex cleanup cases automatically
- Testing cleanup adds unnecessary boilerplate
- Focus tests on data ingestion, not cleanup behavior

### 🛑 When to Stop and Ask

Refactors can be complex. **Stop and ask the user** if you encounter:
- Unclear business logic in legacy Cypher
- Complex relationships that don't map clearly to data model
- Test failures you can't resolve
- Multiple modules that seem interdependent

### 📋 Refactoring Checklist

Before submitting a refactor:

- [ ] ✅ **Integration test exists and passes** for the sync function
- [ ] ✅ **Data model schemas** defined with proper relationships
- [ ] ✅ **Legacy load functions** converted to use `load()`
- [ ] ✅ **Legacy cleanup functions** converted to use `GraphJob.from_node_schema()`
- [ ] ✅ **Tests still pass** after all changes
- [ ] ✅ **Index entries removed** from `indexes.cypher`
- [ ] ✅ **Cleanup JSON files removed** from cleanup directory
- [ ] ✅ **No regressions** - all functionality preserved

### 🎯 Success Criteria

A successful refactor should:
1. **Preserve all functionality** - tests pass
2. **Use data model** - no handwritten Cypher for CRUD operations
3. **Clean up legacy files** - indexes and cleanup jobs removed
4. **Maintain performance** - no significant speed degradation
5. **Follow patterns** - consistent with other modern modules

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
- [ ] ✅ **Testing**: Integration tests for sync functions
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
    make_target_node_matcher, TargetNodeMatcher, OtherRelationships,
    make_source_node_matcher, SourceNodeMatcher  # For MatchLinks
)

# Loading and cleanup
from cartography.client.core.tx import load, load_matchlinks  # load_matchlinks for MatchLinks
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

### MatchLink Pattern (Use Sparingly!)
```python
# Only use for connecting existing nodes or rich relationship properties
@dataclass(frozen=True)
class YourMatchLinkSchema(CartographyRelSchema):
    target_node_label: str = "TargetNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("target_id"),
    })
    source_node_label: str = "SourceNode"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher({
        "id": PropertyRef("source_id"),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: YourMatchLinkRelProperties = YourMatchLinkRelProperties()

# Required properties for MatchLinks
@dataclass(frozen=True)
class YourMatchLinkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    # Your custom properties here

# Load MatchLinks
load_matchlinks(
    neo4j_session,
    YourMatchLinkSchema(),
    mapping_data,
    lastupdated=update_tag,
    _sub_resource_label="AWSAccount",
    _sub_resource_id=account_id,
)

# Cleanup MatchLinks
GraphJob.from_matchlink(
    YourMatchLinkSchema(),
    "AWSAccount",
    account_id,
    update_tag,
).run(neo4j_session)
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
