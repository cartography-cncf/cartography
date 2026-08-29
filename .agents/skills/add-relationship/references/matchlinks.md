# MatchLinks reference

## Contents

- Performance impact
- Scenario 1: connect two existing node types
- Scenario 2: rich relationship properties
- Required MatchLink properties
- MatchLink cleanup
- Optional sub-resource-scoped MatchLinks
- When NOT to use MatchLinks

## Performance impact

MatchLinks are expensive. For each batch, the loader does:

1. (caller) Write source nodes via a previous `load()` call.
2. (caller) Write target nodes via a previous `load()` call.
3. **Read** source node from graph.
4. **Read** target node from graph.
5. **Write** the relationship.

Steps 3–5 are why MatchLinks are slower than relationships defined inside a node schema. Prefer standard relationships whenever a `target_node_matcher` can find the target during normal `load()`.

## Scenario 1: connect two existing node types

When the mapping comes from a separate API call.

```python
role_assignments = [
    {"UserId": "user-123", "IdentityStoreId": "d-9067230b30", "RoleArn": "arn:aws:iam::123456789012:role/AdminRole",    "AccountId": "123456789012"},
    {"UserId": "user-456", "IdentityStoreId": "d-9067230b30", "RoleArn": "arn:aws:iam::123456789012:role/ReadOnlyRole", "AccountId": "123456789012"},
]


@dataclass(frozen=True)
class RoleAssignmentAllowedByMatchLink(CartographyRelSchema):
    # (AWSRole)-[:ALLOWED_BY]->(AWSSSOUser)
    source_node_label: str = "AWSRole"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher({
        "arn": PropertyRef("RoleArn"),
    })
    target_node_label: str = "AWSSSOUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("UserId"),
        "identity_store_id": PropertyRef("IdentityStoreId"),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ALLOWED_BY"
    properties: RoleAssignmentRelProperties = RoleAssignmentRelProperties()


load_matchlinks(
    neo4j_session,
    RoleAssignmentAllowedByMatchLink(),
    role_assignments,
    lastupdated=update_tag,
    _sub_resource_label="AWSAccount",
    _sub_resource_id=aws_account_id,
)
```

## Scenario 2: rich relationship properties

For findings that connect to packages with remediation metadata that doesn't belong on either node.

```python
finding_to_package_data = [
    {
        "findingarn": "arn:aws:inspector2:us-east-1:123456789012:finding/abc123",
        "packageid": "openssl|0:1.1.1k-1.el8.x86_64",
        "filePath": "/usr/lib64/libssl.so.1.1",
        "fixedInVersion": "0:1.1.1l-1.el8",
        "remediation": "Update OpenSSL to version 1.1.1l or later",
    }
]


@dataclass(frozen=True)
class InspectorFindingToPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    filepath: PropertyRef = PropertyRef("filePath")
    fixedinversion: PropertyRef = PropertyRef("fixedInVersion")
    remediation: PropertyRef = PropertyRef("remediation")


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
    rel_label: str = "HAS"
    properties: InspectorFindingToPackageRelProperties = InspectorFindingToPackageRelProperties()
```

## Required MatchLink properties

All MatchLink relationship property classes must include:

```python
@dataclass(frozen=True)
class YourMatchLinkRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)
    # custom rel properties...
```

## MatchLink cleanup

```python
def cleanup(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(YourNodeSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_matchlink(
        YourMatchLinkSchema(),
        "AWSAccount",                       # _sub_resource_label
        common_job_parameters["AWS_ID"],    # _sub_resource_id
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
```

## Optional sub-resource-scoped MatchLinks

When a MatchLink endpoint is only unique within a tenant/account, you can scope the source/target lookup through the sub-resource:

```python
from cartography.models.core.relationships import MatchLinkSubResource


@dataclass(frozen=True)
class YourMatchLinkSchema(CartographyRelSchema):
    # ... normal MatchLink fields ...

    source_node_sub_resource: MatchLinkSubResource = MatchLinkSubResource(
        target_node_label="YourTenant",
        target_node_matcher=make_target_node_matcher({
            "id": PropertyRef("_sub_resource_id", set_in_kwargs=True),
        }),
        direction=LinkDirection.INWARD,
        rel_label="RESOURCE",
    )
```

Without it, the source match looks like:

```cypher
MATCH (from:YourNode {id: item.source_id})
```

With it:

```cypher
MATCH (source_sub_resource:YourTenant {id: $_sub_resource_id})
MATCH (from:YourNode {id: item.source_id})<-[:RESOURCE]-(source_sub_resource)
```

Only enable this when the endpoint is **guaranteed** to be connected to the same sub-resource passed to `load_matchlinks()`. `MatchLinkSubResource.target_node_matcher` must use `PropertyRef(..., set_in_kwargs=True)` because the sub-resource is matched before `UNWIND $DictList AS item`. For broad semantic labels or cross-module labels, review each endpoint separately and only scope the side that is semantically safe.

## When NOT to use MatchLinks

- Standard parent-child relationships -> use `other_relationships` on the node schema.
- Simple one-to-many -> use `PropertyRef(..., one_to_many=True)`.
- Anything definable inside a node schema.
- Performance-critical scenarios.
