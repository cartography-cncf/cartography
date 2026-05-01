# Data model reference

## Contents

- Node properties
- Node schema
- Sub-resource relationships always point to a tenant
- Standard relationship template
- Loading data
- Cleanup
- Manual write queries

## Node properties

```python
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties


@dataclass(frozen=True)
class YourServiceUserNodeProperties(CartographyNodeProperties):
    # Required unique identifier
    id: PropertyRef = PropertyRef("id")

    # Auto-managed by Cartography
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Business fields
    email: PropertyRef = PropertyRef("email", extra_index=True)  # add an index
    name: PropertyRef = PropertyRef("name")
    created_at: PropertyRef = PropertyRef("created_at")
    last_login: PropertyRef = PropertyRef("last_login")
    is_admin: PropertyRef = PropertyRef("is_admin")

    # Same value for every record in the batch
    tenant_id: PropertyRef = PropertyRef("TENANT_ID", set_in_kwargs=True)
```

`PropertyRef` parameters:
- First arg: key in the per-record dict, **or** kwarg name when `set_in_kwargs=True`.
- `extra_index=True` — add a database index for query performance.
- `set_in_kwargs=True` — value comes from `load(..., KWARG=value)`, not the per-record dict.

For advanced node features (extra labels, conditional labels, scoped cleanup, one-to-many) see the `add-node-type` skill.

## Node schema

```python
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import OtherRelationships


@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
    other_relationships: OtherRelationships = OtherRelationships([
        YourServiceUserToHumanRel(),
    ])
```

## Sub-resource relationships always point to a tenant

For child resources, the `sub_resource_relationship` must point to a tenant-like node, the ownership / organisational boundary used for cleanup. Root-level / global feed schemas (e.g. the tenant itself, or shared threat-intel data) intentionally leave `sub_resource_relationship` unset and pair that with `scoped_cleanup = False`.

| Provider           | Tenant-like node          |
| ------------------ | ------------------------- |
| AWS                | `AWSAccount`              |
| Azure              | `AzureSubscription`       |
| GCP                | `GCPProject`              |
| GitHub             | `GitHubOrganization`      |
| SaaS               | `<Service>Tenant`         |

**Wrong:** pointing to an infrastructure parent (e.g. `ECSContainer -> ECSTask`) or a logical grouping that is not an organisational boundary.

### Why

- **Cleanup**: Cartography uses the sub-resource relationship to scope `GraphJob.from_node_schema()` cleanups.
- **Organisation**: tenant-like objects provide the natural data boundary.
- **Access control**: tenant edges enable proper isolation.

### ECS container definition example (correct)

```python
@dataclass(frozen=True)
class ECSContainerDefinitionSchema(CartographyNodeSchema):
    label: str = "ECSContainerDefinition"
    properties: ECSContainerDefinitionNodeProperties = ECSContainerDefinitionNodeProperties()
    sub_resource_relationship: ECSContainerDefinitionToAWSAccountRel = ECSContainerDefinitionToAWSAccountRel()  # tenant
    other_relationships: OtherRelationships = OtherRelationships([
        ECSContainerDefinitionToTaskDefinitionRel(),  # business relationship
    ])


@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("AWS_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerDefinitionToAWSAccountRelProperties = ECSContainerDefinitionToAWSAccountRelProperties()
```

## Standard relationship template

```python
from cartography.models.core.relationships import (
    CartographyRelSchema, CartographyRelProperties, LinkDirection,
    make_target_node_matcher, TargetNodeMatcher,
)


@dataclass(frozen=True)
class YourServiceTenantToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class YourServiceTenantToUserRel(CartographyRelSchema):
    target_node_label: str = "YourServiceTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("TENANT_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: YourServiceTenantToUserRelProperties = YourServiceTenantToUserRelProperties()
```

Direction:
- `LinkDirection.INWARD`: `(:YourServiceTenant)-[:RESOURCE]->(:YourServiceUser)` — used for sub-resource relationships.
- `LinkDirection.OUTWARD`: `(:YourServiceUser)-[:RESOURCE]->(:YourServiceTenant)` — rare for `RESOURCE`.

For MatchLinks, one-to-many, and multi-module patterns see the `add-relationship` skill.

## Loading data

```python
from cartography.client.core.tx import load


def load_users(neo4j_session, data, tenant_id, update_tag):
    # Load tenant first if it doesn't already exist.
    load(neo4j_session, YourServiceTenantSchema(), [{"id": tenant_id}], lastupdated=update_tag)

    # Then load users with the relationship to the tenant.
    load(
        neo4j_session,
        YourServiceUserSchema(),
        data,
        lastupdated=update_tag,
        TENANT_ID=tenant_id,  # available as PropertyRef("TENANT_ID", set_in_kwargs=True)
    )
```

## Cleanup

```python
from cartography.graph.job import GraphJob


def cleanup(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(YourServiceUserSchema(), common_job_parameters).run(neo4j_session)
```

## Manual write queries

If you must execute a hand-written Cypher write, use `run_write_query()`. Reserve `neo4j_session.run()` for read-only queries or intentional low-level paths that cannot use the managed write helpers.
