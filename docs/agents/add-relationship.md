# Adding a New Relationship

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Add Node Type](add-node-type.md)

This guide covers how to define relationships in Cartography, including standard relationships, MatchLinks for connecting existing nodes, and patterns for multiple modules modifying the same node type.

## Standard Relationships

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

## Relationship Directions

- `LinkDirection.OUTWARD`: `(:YourServiceUser)-[:RESOURCE]->(:YourServiceTenant)`
- `LinkDirection.INWARD`: `(:YourServiceUser)<-[:RESOURCE]-(:YourServiceTenant)`

## One-to-Many Relationships

When you need to connect one node to many others:

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

---

## MatchLinks: Connecting Existing Nodes

**IMPORTANT: Use MatchLinks sparingly due to performance impact!**

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

### Performance Impact

MatchLinks have significant performance overhead because they require:

1. **API Call A** -> Write Node A to graph
2. **API Call B** -> Write Node B to graph
3. **Read Node A** from graph
4. **Read Node B** from graph
5. **Write relationship** between A and B to graph

**Prefer standard node schemas + relationship schemas** whenever possible:

```python
# DO: Use standard node schema with relationships
@dataclass(frozen=True)
class YourNodeSchema(CartographyNodeSchema):
    label: str = "YourNode"
    properties: YourNodeProperties = YourNodeProperties()
    sub_resource_relationship: YourNodeToTenantRel = YourNodeToTenantRel()
    other_relationships: OtherRelationships = OtherRelationships([
        YourNodeToOtherNodeRel(),  # Standard relationship
    ])

# DON'T: Use MatchLinks unless absolutely necessary
# Only use when you can't define the relationship in the node schema
```

### When NOT to Use MatchLinks

**Don't use MatchLinks for:**
- Standard parent-child relationships (use `other_relationships` in node schema)
- Simple one-to-many relationships (use `one_to_many=True` in standard relationships)
- When you can define the relationship in the node schema
- Performance-critical scenarios

**Use MatchLinks only for:**
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

---

## Multiple Intel Modules Modifying the Same Node Type

It is possible (and encouraged) for more than one intel module to modify the same node type. However, there are two distinct patterns for this:

### Simple Relationship Pattern

When data type A only refers to data type B by an ID without providing additional properties about B, we can just define a relationship schema. This way when A is loaded, the relationship schema performs a `MATCH` to find and connect to existing nodes of type B.

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

### Composite Node Pattern

When a data type A refers to another data type B and offers additional fields about B that B doesn't have itself, we should define a composite node schema. This composite node would be named "`BASchema`" to denote that it's a "`B`" object as known by an "`A`" object. When loaded, the composite node schema targets the same node label as the primary `B` schema, allowing the loading system to perform a `MERGE` operation that combines properties from both sources.

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

---

## Common Patterns

### Pattern 1: Simple Service with Users (LastPass Style)

```python
# Data flow
API Response -> transform() -> [{"id": "123", "email": "user@example.com", ...}] -> load()

# Key characteristics:
- One main entity type (users)
- Simple tenant relationship
- Standard fields (id, email, created_at, etc.)
```

### Pattern 2: Complex Infrastructure (AWS EC2 Style)

```python
# Data flow
API Response -> transform() -> Multiple lists -> Multiple load() calls

# Key characteristics:
- Multiple entity types (instances, security groups, subnets)
- Complex relationships between entities
- Regional/account-scoped resources
```

### Pattern 3: Hierarchical Resources (Route Tables Style)

```python
# One-to-many transformation
{
    "RouteTableId": "rtb-123",
    "Associations": [{"SubnetId": "subnet-abc"}, {"SubnetId": "subnet-def"}]
}
->
{
    "id": "rtb-123",
    "subnet_ids": ["subnet-abc", "subnet-def"]  # Flattened for one_to_many
}
```
