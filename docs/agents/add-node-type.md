# Adding a New Node Type

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Add Relationship](add-relationship.md)

This guide covers advanced node schema properties, including extra labels, scoped cleanup, one-to-many relationships, and common mistakes to avoid.

## Node Properties

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

## Node Schema

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

## Advanced Node Schema Properties

### Extra Node Labels

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

### Conditional Node Labels

> **Warning**: Conditional labels are a specialized feature primarily used for ontology mapping scenarios where a single data source produces records that map to different semantic types. Most intel modules do not need this feature.

Sometimes you want to apply labels only when certain conditions are met. Use `ConditionalNodeLabel` for this:

```python
from cartography.models.core.nodes import ConditionalNodeLabel, ExtraNodeLabels

@dataclass(frozen=True)
class ECRImageSchema(CartographyNodeSchema):
    label: str = "ECRImage"
    properties: ECRImageNodeProperties = ECRImageNodeProperties()
    sub_resource_relationship: ECRImageToAccountRel = ECRImageToAccountRel()

    # Apply different ontology labels based on the image type
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([
        ConditionalNodeLabel(
            label="Image",
            conditions={"type": "IMAGE"}
        ),
        ConditionalNodeLabel(
            label="ImageAttestation",
            conditions={"type": "IMAGE_ATTESTATION"}
        ),
        ConditionalNodeLabel(
            label="ImageManifestList",
            conditions={"type": "IMAGE_MANIFEST_LIST"}
        ),
    ])
```

**Primary use case: Container Registry Images**

ECR (and other container registries) store different types of artifacts that share the same base schema but have fundamentally different semantic meanings:

| `type` field value | Ontology Label | Description |
|-------------------|----------------|-------------|
| `IMAGE` | `Image` | Standard container image |
| `IMAGE_ATTESTATION` | `ImageAttestation` | SLSA/Sigstore attestation |
| `IMAGE_MANIFEST_LIST` | `ImageManifestList` | Multi-arch manifest list |

Without conditional labels, we cannot accurately map these to distinct ontology types. An `ECRImage` node with `type: "IMAGE_ATTESTATION"` should be labeled as `ImageAttestation` in the ontology, not just generic `Image`.

**How it works:**
- String labels (like `"SecurityFinding"`) are applied unconditionally to all nodes during ingestion
- `ConditionalNodeLabel` labels are applied in a separate query after ingestion, only to nodes matching all specified conditions
- Conditions use exact string equality and are combined with AND logic
- When conditions change, labels are automatically added or removed on subsequent syncs

**Important notes:**
- Condition values must be strings (e.g., `"true"` not `True`)
- All conditions must match for the label to be applied (AND logic)
- Indexes are automatically created for conditional labels and their condition fields

### Scoped Cleanup

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

**When to Override `scoped_cleanup`:**

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

## One-to-Many Relationships

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

## Common Schema Mistakes to Avoid

**DO NOT add custom properties to `CartographyRelSchema` or `CartographyNodeSchema` subclasses**: These dataclasses are processed by Cartography's core loading system, which only recognizes the standard fields defined in the base classes. Any additional fields you add will be ignored and have no effect.

```python
# DON'T do this - custom fields are ignored by the loading system
@dataclass(frozen=True)
class MyRelationship(CartographyRelSchema):
    target_node_label: str = "SomeNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("some_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()
    # These custom fields do nothing:
    conditional_match_property: str = "some_id"
    custom_flag: bool = True
    extra_config: dict = {"key": "value"}

# DON'T do this either - custom fields on node schemas are also ignored
@dataclass(frozen=True)
class MyNodeSchema(CartographyNodeSchema):
    label: str = "MyNode"
    properties: MyNodeProperties = MyNodeProperties()
    sub_resource_relationship: MyRel = MyRel()
    # This custom field does nothing:
    custom_setting: str = "ignored"

# DO this instead - stick to the standard schema fields only
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
    scoped_cleanup: bool = True  # Optional, defaults to True
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

## Sub-Resource Relationships: Always Point to Tenant-Like Objects

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

**Why This Matters:**
1. **Cleanup Operations**: Cartography uses the sub-resource relationship to determine which data to clean up during sync operations
2. **Data Organization**: Tenant-like objects provide natural boundaries for data organization
3. **Access Control**: Tenant relationships enable proper access control and data isolation
4. **Consistency**: Following this pattern ensures consistent data modeling across all modules

## Loading Data

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

## Required Node Properties

Every node must have these properties:

```python
@dataclass(frozen=True)
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")                                    # REQUIRED: Unique identifier
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)  # REQUIRED: Auto-managed
    # Your business properties here...
```

## Date Handling

Neo4j 4+ supports native Python datetime objects and ISO 8601 formatted strings. Avoid manual datetime parsing:

```python
# DON'T: Manually parse dates or convert to epoch timestamps
"created_at": int(dt_parse.parse(user_data["created_at"]).timestamp() * 1000)
"last_login": dict_date_to_epoch({"d": dt_parse.parse(data["last_login"])}, "d")

# DO: Pass datetime values directly
"created_at": user_data.get("created_at")  # AWS/API returns ISO 8601 dates
"last_login": user_data.get("last_login")  # Neo4j handles these natively
```
