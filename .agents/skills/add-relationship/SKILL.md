---
name: add-relationship
description: Define a `CartographyRelSchema` (standard relationship), one-to-many edge, or `MatchLink` connecting existing nodes. Use when the user asks to add a relationship, link nodes, set a `RESOURCE` / `MEMBER_OF` / `ASSOCIATED_WITH` edge, share a node across modules, or model a composite node from two intel sources.
---

# add-relationship

Add a relationship between Cartography nodes. Cover three flavours:

1. **Standard relationship** on a node schema (`other_relationships` or `sub_resource_relationship`).
2. **One-to-many** with `PropertyRef(..., one_to_many=True)`.
3. **MatchLink** for connecting two **already-existing** nodes — use sparingly.

## Critical rules

1. **Prefer standard relationships** in node schemas. MatchLinks have a real performance cost (extra `MATCH` reads).
2. **Use MatchLinks only when:** the relationship data comes from a separate source and connects two existing node types, **or** the relationship needs rich metadata that doesn't belong on either node.
3. **MatchLink relationship properties must include `lastupdated`, `_sub_resource_label`, `_sub_resource_id`** (all `set_in_kwargs=True`).
4. **Always implement cleanup.** Standard rels: `GraphJob.from_node_schema()`. MatchLinks: `GraphJob.from_matchlink()`.
5. **`sub_resource_relationship` always points to a tenant-like node.** See the `add-node-type` skill.

## Instructions

### Step 1 — Standard relationship

Define rel properties (typically just `lastupdated`) and the relationship itself, then attach it to a node schema via `sub_resource_relationship` (tenant link) or `other_relationships` (business link).

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
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: YourServiceTenantToUserRelProperties = YourServiceTenantToUserRelProperties()
```

### Step 2 — Pick a direction

- `LinkDirection.OUTWARD`: `(:Source)-[:REL]->(:Target)`
- `LinkDirection.INWARD`:  `(:Source)<-[:REL]-(:Target)`

Sub-resource relationships use `INWARD` (`(:Tenant)-[:RESOURCE]->(:Resource)` from the tenant's POV is `INWARD` for the resource side).

### Step 3 — One-to-many

Flatten target IDs in `transform()` and use `one_to_many=True`:

```python
# transform
{"id": "rtb-123", "subnet_ids": ["subnet-abc", "subnet-def"]}

# rel
@dataclass(frozen=True)
class RouteTableToSubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "subnet_id": PropertyRef("subnet_ids", one_to_many=True),
    })
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSOCIATED_WITH"
    properties: RouteTableToSubnetRelProperties = RouteTableToSubnetRelProperties()
```

Cartography expands `one_to_many` into one edge per ID in the list.

### Step 4 — Decide whether you need a MatchLink

**Use a MatchLink when:**
- The relationship comes from a **separate API call / data source** that maps two already-loaded node types.
- The relationship needs **rich metadata** (e.g. CVE remediation details, fix version, file path) that doesn't belong on either node.

**Don't use MatchLinks for:**
- Standard parent-child relationships (use `other_relationships`).
- Simple one-to-many (use `one_to_many=True`).
- Cases where the relationship can be defined inside the node schema.
- Performance-critical paths.

### Step 5 — MatchLink schema

```python
from cartography.models.core.relationships import (
    CartographyRelSchema, CartographyRelProperties, LinkDirection,
    make_target_node_matcher, TargetNodeMatcher,
    make_source_node_matcher, SourceNodeMatcher,
)


@dataclass(frozen=True)
class RoleAssignmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef("_sub_resource_label", set_in_kwargs=True)
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


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
```

### Step 6 — Load + cleanup MatchLinks

```python
load_matchlinks(
    neo4j_session,
    RoleAssignmentAllowedByMatchLink(),
    role_assignments,
    lastupdated=update_tag,
    _sub_resource_label="AWSAccount",
    _sub_resource_id=aws_account_id,
)


def cleanup(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(YourNodeSchema(), common_job_parameters).run(neo4j_session)
    GraphJob.from_matchlink(
        YourMatchLinkSchema(),
        "AWSAccount",                      # _sub_resource_label
        common_job_parameters["AWS_ID"],   # _sub_resource_id
        common_job_parameters["UPDATE_TAG"],
    ).run(neo4j_session)
```

For richer MatchLink scenarios (rich rel properties, optional `MatchLinkSubResource` scoping, multi-module composite nodes), see `references/matchlinks.md` and `references/multi-module-patterns.md`.

## Common issues

- `Relationship not created` — the target node didn't exist when the rel was loaded. Load parent nodes first.
- Matcher property mismatch — `target_node_matcher` keys must match the **target node's** property names (e.g. `id`, `arn`).
- MatchLink misses — both source and target nodes must already exist before `load_matchlinks()`.
- Cleanup deletes too much — confirm `_sub_resource_id` and `UPDATE_TAG` in `common_job_parameters`.

For the full troubleshooting list, see the `troubleshooting` skill.

## References (load on demand)

- `references/matchlinks.md` — MatchLink performance impact, rich-property example (Inspector findings), `MatchLinkSubResource` scoping.
- `references/multi-module-patterns.md` — simple-relationship vs composite-node patterns when multiple intel modules touch the same node label.
