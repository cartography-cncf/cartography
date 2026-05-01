---
name: add-node-type
description: Define a new node schema under cartography/models/MODULE_NAME/, including required properties, sub-resource relationships, extra labels, conditional labels, scoped cleanup, and one-to-many transforms. Use when the user asks to add a node type, model a new resource, configure extra Neo4j labels (Identity, Asset, UserAccount, Tenant), or wire scoped vs global cleanup.
---

# add-node-type

Add a new `CartographyNodeSchema` (and its `CartographyNodeProperties`) to a Cartography module. This skill assumes the surrounding module already exists; for end-to-end module creation, see the `create-module` skill.

## Critical rules

1. **`@dataclass(frozen=True)` everywhere**, with type annotations on every field (`x: PropertyRef = PropertyRef("x")`). A missing annotation triggers `PropertyRef validation failed`.
2. **Only the standard schema fields are recognised.** Custom fields on `CartographyNodeSchema` / `CartographyRelSchema` subclasses are silently ignored — see "Standard fields" below.
3. **`sub_resource_relationship` always points to a tenant-like node** (`AWSAccount`, `AzureSubscription`, `GCPProject`, `GitHubOrganization`, your `<Service>Tenant`).
4. **`scoped_cleanup` defaults to `True`.** Override to `False` only for genuinely global data (CVE feeds, public threat intel, public DNS).

## Instructions

### Step 1 — Required properties

Every node type needs at least:

```python
@dataclass(frozen=True)
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")                                       # REQUIRED
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True) # REQUIRED
    # business properties...
```

`PropertyRef` parameters:
- First arg: per-record dict key, **or** kwarg name when `set_in_kwargs=True`.
- `extra_index=True` — add a database index for query performance.
- `set_in_kwargs=True` — value comes from `load(..., KWARG=...)`, not the per-record dict.
- `one_to_many=True` — value is a list; expand to many edges (see "One-to-many" below).

### Step 2 — Schema with sub-resource relationship

```python
@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
    other_relationships: OtherRelationships = OtherRelationships([
        YourServiceUserToHumanRel(),
    ])
```

### Step 3 — Pick the right standard fields

`CartographyNodeSchema` standard fields:

| Field                       | Type                              | Required | Notes                                                       |
| --------------------------- | --------------------------------- | :------: | ----------------------------------------------------------- |
| `label`                     | `str`                             | Yes      | Neo4j node label                                            |
| `properties`                | `CartographyNodeProperties` subclass | Yes   |                                                             |
| `sub_resource_relationship` | `CartographyRelSchema` subclass   | Yes      | Tenant-like target. `None` only if `scoped_cleanup=False`.  |
| `other_relationships`       | `OtherRelationships`              | No       | Additional business relationships                           |
| `extra_node_labels`         | `ExtraNodeLabels`                 | No       | Additional Neo4j labels (e.g. `Identity`, `UserAccount`)    |
| `scoped_cleanup`            | `bool`                            | No       | Defaults to `True`. Almost never override.                  |

`CartographyRelSchema` standard fields: `target_node_label`, `target_node_matcher`, `direction`, `rel_label`, `properties`. Custom fields **do nothing** — handle conditional behaviour in `transform()` by setting fields to `None` or filtering before `load()`.

### Step 4 — Extra labels

Add additional Neo4j labels with `ExtraNodeLabels`:

```python
from cartography.models.core.nodes import ExtraNodeLabels

extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Identity", "Asset"])
```

Produces `(:YourServiceUser:Identity:Asset)`. For ontology-driven labels (`UserAccount`, `Tenant`, `Database`, ...) see the `enrich-ontology` skill.

### Step 5 — Decide on `scoped_cleanup`

Default behaviour `scoped_cleanup=True` is correct for almost everything: user accounts, infrastructure resources, application assets — anything scoped to a tenant.

Override to `False` only for genuinely global data with no tenant:

```python
@dataclass(frozen=True)
class VulnerabilitySchema(CartographyNodeSchema):
    label: str = "Vulnerability"
    properties: VulnerabilityNodeProperties = VulnerabilityNodeProperties()
    sub_resource_relationship: None = None
    scoped_cleanup: bool = False
```

Examples that justify `scoped_cleanup=False`: CVE databases, threat intel feeds, public certificate transparency logs, global DNS / domain info.

### Step 6 — One-to-many

When one source record points to many targets, flatten the IDs in `transform()` and use `one_to_many=True` on the relationship matcher:

```python
# transform
def transform_route_tables(route_tables):
    out = []
    for rt in route_tables:
        out.append({
            "id": rt["RouteTableId"],
            "subnet_ids": [a["SubnetId"] for a in rt.get("Associations", []) if "SubnetId" in a],
        })
    return out


# relationship
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

### Step 7 — Date handling

Neo4j 4+ supports native datetimes and ISO 8601 strings. Pass values through directly — do not convert to epoch milliseconds.

```python
# DO
"created_at": user_data.get("created_at")

# DON'T
"created_at": int(dt_parse.parse(user_data["created_at"]).timestamp() * 1000)
```

### Step 8 — Loading

```python
from cartography.client.core.tx import load

load(neo4j_session, YourServiceTenantSchema(), [{"id": tenant_id}], lastupdated=update_tag)
load(
    neo4j_session,
    YourServiceUserSchema(),
    data,
    lastupdated=update_tag,
    TENANT_ID=tenant_id,
)
```

## Common issues

- `PropertyRef validation failed` — missing `frozen=True` or missing type annotation.
- Custom field on a `Schema` is "ignored" — only standard fields are recognised.
- Cleanup deleting too much / too little — verify `scoped_cleanup` and `common_job_parameters["TENANT_ID"]`.

For the full troubleshooting list, see the `troubleshooting` skill.

## References (load on demand)

- `references/advanced-properties.md` — conditional labels (ECR images / attestations), MatchLink targets, deeper sub-resource rationale, ECS example.
