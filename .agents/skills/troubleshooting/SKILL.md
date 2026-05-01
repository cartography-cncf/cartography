---
name: troubleshooting
description: Diagnose and fix common Cartography intel-module errors — `ModuleNotFoundError`, `PropertyRef validation failed`, `GraphJob failed`, missing relationships, MatchLink misses, cleanup deleting too much, slow queries, ignored custom schema fields, key errors during transform. Use when the user reports an error while developing or running a Cartography module.
---

# troubleshooting

Diagnostic playbook for the most common errors encountered while developing Cartography intel modules.

## Common issues and solutions

### Import errors

```python
# Problem: ModuleNotFoundError for your new module
# Solution: ensure __init__.py files exist in all directories
cartography/intel/your_service/__init__.py
cartography/models/your_service/__init__.py
```

Checklist:

- [ ] `__init__.py` exists in `cartography/intel/your_service/`
- [ ] `__init__.py` exists in `cartography/models/your_service/`
- [ ] Module is imported in the parent `__init__.py` if needed

### Schema validation errors

```python
# Problem: "PropertyRef validation failed"
# Solution: check dataclass syntax and PropertyRef definitions
@dataclass(frozen=True)  # do not forget frozen=True
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")  # must have type annotation
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
```

Common causes:

- Missing `frozen=True` in `@dataclass`.
- Missing type annotation (`: PropertyRef`).
- Typo in the `PropertyRef` field name.

### Relationship connection issues

```python
# Problem: relationships not created
# Solution: ensure target nodes exist before creating relationships

# Load parent nodes first:
load(neo4j_session, TenantSchema(), tenant_data, lastupdated=update_tag)

# Then load child nodes with relationships:
load(neo4j_session, UserSchema(), user_data, lastupdated=update_tag, TENANT_ID=tenant_id)
```

Debugging steps:

1. Check the target node label matches exactly.
2. Verify `target_node_matcher` keys match the **target node's** property names.
3. Ensure the value in your data dict or kwargs is not `None`.

### Cleanup job failures

```python
# Problem: "GraphJob failed" during cleanup
# Solution: check common_job_parameters
common_job_parameters = {
    "UPDATE_TAG": config.update_tag,  # must match what is set on nodes
    "TENANT_ID": tenant_id,           # if using scoped cleanup (default)
}
```

```python
# Problem: cleanup deletes too much (wrong scoped_cleanup setting)
# Solution: verify scoped_cleanup is appropriate

@dataclass(frozen=True)
class MySchema(CartographyNodeSchema):
    # tenant-scoped resources — default, do not specify
    # scoped_cleanup: bool = True

    # global resources only — rare
    scoped_cleanup: bool = False  # vuln data, threat intel, etc.
```

For details on when to override `scoped_cleanup`, see the `add-node-type` skill.

### Data transform issues

```python
# Problem: KeyError during transform
# Solution: handle required vs optional fields correctly
{
    "id": data["id"],              # required — let it fail
    "name": data.get("name"),      # optional
    # avoid empty-string defaults — they hide missing data
    # "email": data.get("email", ""),
    "email": data.get("email"),    # use None default
}
```

### Schema definition issues

```python
# Problem: adding custom fields to schema classes
# Solution: remove them — only standard fields are recognised

@dataclass(frozen=True)
class MyRel(CartographyRelSchema):
    # Remove custom fields — they are silently ignored:
    # conditional_match_property: str = "some_field"
    # custom_flag: bool = True
    # extra_config: dict = {}

    # Keep only the standard relationship fields
    target_node_label: str = "TargetNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(...)
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()
```

For the standard schema fields, see the `add-node-type` skill.

### Performance issues

```python
# Problem: slow queries
# Solution: index frequently queried fields
email: PropertyRef = PropertyRef("email", extra_index=True)

# Query on indexed fields when possible
MATCH (u:User {id: $user_id})  # good — id is always indexed
MATCH (u:User {name: $name})   # bad — name might not be indexed
```

Fields used inside a `target_node_matcher` are indexed automatically.

### MatchLink issues

```python
# Problem: MatchLinks not creating relationships
# Solution: both source and target nodes must exist first

load(neo4j_session, SourceNodeSchema(), source_data, ...)   # 1. source nodes
load(neo4j_session, TargetNodeSchema(), target_data, ...)   # 2. target nodes

load_matchlinks(                                            # 3. then MatchLinks
    neo4j_session,
    YourMatchLinkSchema(),
    mapping_data,
    lastupdated=update_tag,
    _sub_resource_label="AWSAccount",
    _sub_resource_id=account_id,
)
```

```python
# Problem: MatchLink cleanup not working
# Solution: use GraphJob.from_matchlink with the right args
GraphJob.from_matchlink(
    YourMatchLinkSchema(),
    "AWSAccount",                          # _sub_resource_label
    common_job_parameters["AWS_ID"],       # _sub_resource_id
    common_job_parameters["UPDATE_TAG"],   # update_tag
).run(neo4j_session)
```

For full MatchLink details, see the `add-relationship` skill.

## Debugging tips

1. **Check existing patterns first.** Look at similar modules in `cartography/intel/` before inventing new ones.
2. **Verify imports.** All `CartographyNodeSchema` / `CartographyRelSchema` imports must point to `cartography.models.core.*`.
3. **Test transform functions** with real API responses.
4. **Validate Cypher in Neo4j Browser** when relationships are not appearing.
5. **Check file naming.** Module files should match the service name (`cartography/intel/lastpass/users.py`).
6. **Run tests incrementally.** After each change, run the integration test.
7. **Test through `sync()`**, not isolated `load()` calls.

## Key files

| File                                          | Purpose                                                                       |
| --------------------------------------------- | ----------------------------------------------------------------------------- |
| `cartography/client/core/tx.py`               | Core `load()` and `load_matchlinks()` — query generation lives here           |
| `cartography/graph/job.py`                    | `GraphJob` cleanup operations                                                 |
| `cartography/models/core/common.py`           | `PropertyRef` definition                                                      |
| `cartography/models/core/nodes.py`            | `CartographyNodeSchema`, `CartographyNodeProperties`, `ExtraNodeLabels`, etc. |
| `cartography/models/core/relationships.py`    | `CartographyRelSchema`, `LinkDirection`, matchers, MatchLinks                 |
| `cartography/config.py`                       | `Config` object — check missing fields here                                   |
| `cartography/cli.py`                          | Typer CLI with help panels                                                    |
| `cartography/data/indexes.cypher`             | Manual index definitions (legacy)                                             |
| `cartography/data/jobs/cleanup/`              | Legacy cleanup JSON files                                                     |
| `cartography/data/jobs/analysis/`             | Global analysis JSON files (see `analysis-jobs` skill)                         |
| `cartography/data/jobs/scoped_analysis/`      | Scoped analysis JSON files                                                     |

## Test utilities

```python
from tests.integration.util import check_nodes, check_rels


# Nodes
expected_nodes = {
    ("user-123", "alice@example.com"),
    ("user-456", "bob@example.com"),
}
assert check_nodes(neo4j_session, "YourServiceUser", ["id", "email"]) == expected_nodes


# Relationships
expected_rels = {
    ("user-123", "tenant-123"),
    ("user-456", "tenant-123"),
}
assert check_rels(
    neo4j_session,
    "YourServiceUser", "id",
    "YourServiceTenant", "id",
    "RESOURCE",
    rel_direction_right=True,
) == expected_rels
```

## Error message reference

| Error message                       | Likely cause                                | Solution                                       |
| ----------------------------------- | ------------------------------------------- | ---------------------------------------------- |
| `PropertyRef validation failed`     | Missing type annotation or `frozen=True`    | Check dataclass definition                     |
| `Node not found for relationship`   | Target node does not exist                  | Load parent nodes first                        |
| `GraphJob failed`                   | Wrong `common_job_parameters`               | Check `UPDATE_TAG` and tenant ID               |
| `KeyError: 'field_name'`            | Required field missing in API response      | Use `.get()` for optional fields               |
| `ModuleNotFoundError`               | Missing `__init__.py`                       | Add `__init__.py` to all directories           |
| `Relationship not created`          | Matcher property mismatch                   | Verify property names match exactly            |

## When to ask for help

Stop and ask the user when:

- Legacy Cypher queries contain unclear business logic.
- Complex relationships do not map clearly to the data model.
- Tests keep failing after multiple attempts.
- Multiple modules look interdependent.
- Performance issues persist after adding indexes.
- The graph contains unexpected data after sync.
