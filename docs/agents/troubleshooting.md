# Troubleshooting Guide

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Add Node Type](add-node-type.md)

This guide helps you diagnose and fix common issues when developing Cartography intel modules.

## Common Issues and Solutions

### Import Errors

```python
# Problem: ModuleNotFoundError for your new module
# Solution: Ensure __init__.py files exist in all directories
cartography/intel/your_service/__init__.py
cartography/models/your_service/__init__.py
```

**Checklist:**
- [ ] `__init__.py` exists in `cartography/intel/your_service/`
- [ ] `__init__.py` exists in `cartography/models/your_service/`
- [ ] Module is imported in parent `__init__.py` if needed

### Schema Validation Errors

```python
# Problem: "PropertyRef validation failed"
# Solution: Check dataclass syntax and PropertyRef definitions
@dataclass(frozen=True)  # Don't forget frozen=True!
class YourNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")  # Must have type annotation
```

**Common causes:**
- Missing `frozen=True` in `@dataclass` decorator
- Missing type annotation (`: PropertyRef`)
- Typo in PropertyRef field name

### Relationship Connection Issues

```python
# Problem: Relationships not created
# Solution: Ensure target nodes exist before creating relationships

# Load parent nodes first:
load(neo4j_session, TenantSchema(), tenant_data, lastupdated=update_tag)

# Then load child nodes with relationships:
load(neo4j_session, UserSchema(), user_data, lastupdated=update_tag, TENANT_ID=tenant_id)
```

**Debugging steps:**
1. Check that the target node label matches exactly
2. Verify the `target_node_matcher` property name matches the target node's property
3. Ensure the value in your data dict or kwargs is not `None`

### Cleanup Job Failures

```python
# Problem: "GraphJob failed" during cleanup
# Solution: Check common_job_parameters structure
common_job_parameters = {
    "UPDATE_TAG": config.update_tag,  # Must match what's set on nodes
    "TENANT_ID": tenant_id,           # If using scoped cleanup (default)
}
```

```python
# Problem: Cleanup deleting too much data (wrong scoped_cleanup setting)
# Solution: Verify scoped_cleanup setting is appropriate

@dataclass(frozen=True)
class MySchema(CartographyNodeSchema):
    # For tenant-scoped resources (default, most common):
    # scoped_cleanup: bool = True  # Default - no need to specify

    # For global resources only (rare):
    scoped_cleanup: bool = False  # Only for vuln data, threat intel, etc.
```

### Data Transform Issues

```python
# Problem: KeyError during transform
# Solution: Handle required vs optional fields correctly
{
    "id": data["id"],                    # Required - let it fail
    "name": data.get("name"),            # Optional - use .get()
    "email": data.get("email", ""),      # DON'T use empty string default
    "email": data.get("email"),          # DO use None default
}
```

### Schema Definition Issues

```python
# Problem: Adding custom fields to schema classes
# Solution: Remove them - only standard fields are recognized by the loading system

@dataclass(frozen=True)
class MyRel(CartographyRelSchema):
    # Remove any custom fields like these:
    # conditional_match_property: str = "some_field"  # Ignored
    # custom_flag: bool = True                        # Ignored
    # extra_config: dict = {}                         # Ignored

    # Keep only the standard relationship fields
    target_node_label: str = "TargetNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(...)
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()
```

### Performance Issues

```python
# Problem: Slow queries
# Solution: Add indexes to frequently queried fields
email: PropertyRef = PropertyRef("email", extra_index=True)

# Query on indexed fields only
MATCH (u:User {id: $user_id})  # Good - id is always indexed
MATCH (u:User {name: $name})   # Bad - name might not be indexed
```

**Note:** Fields referred to in a `target_node_matcher` are indexed automatically.

### MatchLink Issues

```python
# Problem: MatchLinks not creating relationships
# Solution: Ensure both source and target nodes exist first

# 1. Load source nodes
load(neo4j_session, SourceNodeSchema(), source_data, ...)

# 2. Load target nodes
load(neo4j_session, TargetNodeSchema(), target_data, ...)

# 3. Then load matchlinks
load_matchlinks(
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
# Solution: Use GraphJob.from_matchlink() with correct parameters
GraphJob.from_matchlink(
    YourMatchLinkSchema(),
    "AWSAccount",                          # _sub_resource_label
    common_job_parameters["AWS_ID"],       # _sub_resource_id
    common_job_parameters["UPDATE_TAG"],   # update_tag
).run(neo4j_session)
```

---

## Debugging Tips for AI Assistants

1. **Check existing patterns first**: Look at similar modules in `cartography/intel/` before creating new patterns

2. **Verify data model imports**: Ensure all `CartographyNodeSchema` imports are correct

3. **Test transform functions**: Always test data transformation logic with real API responses

4. **Validate Neo4j queries**: Use Neo4j browser to test queries manually if relationships aren't working

5. **Check file naming**: Module files should match the service name (e.g., `cartography/intel/lastpass/users.py`)

6. **Run tests incrementally**: After each change, run the integration test to catch issues early

7. **Use the sync function**: Always test through the `sync()` function, not individual `load()` calls

---

## Key Files for Debugging

Understanding these files helps diagnose issues:

| File | Purpose |
|------|---------|
| `cartography/client/core/tx.py` | Core `load()` and `load_matchlinks()` functions - check for query generation issues |
| `cartography/graph/job.py` | `GraphJob` class for cleanup operations |
| `cartography/models/core/common.py` | `PropertyRef` class definition |
| `cartography/models/core/nodes.py` | `CartographyNodeSchema`, `CartographyNodeProperties` base classes |
| `cartography/models/core/relationships.py` | `CartographyRelSchema`, `LinkDirection`, matchers |
| `cartography/config.py` | Configuration object - check for missing fields |
| `cartography/cli.py` | CLI argument definitions |
| `cartography/data/indexes.cypher` | Manual index definitions (legacy) |
| `cartography/data/jobs/cleanup/` | Legacy cleanup job JSON files |

---

## Test Utilities

Use these utilities in integration tests:

```python
from tests.integration.util import check_nodes, check_rels

# Check nodes exist with expected properties
expected_nodes = {
    ("user-123", "alice@example.com"),
    ("user-456", "bob@example.com"),
}
assert check_nodes(neo4j_session, "YourServiceUser", ["id", "email"]) == expected_nodes

# Check relationships exist
expected_rels = {
    ("user-123", "tenant-123"),
    ("user-456", "tenant-123"),
}
assert check_rels(
    neo4j_session,
    "YourServiceUser",      # Source node label
    "id",                   # Source node property
    "YourServiceTenant",    # Target node label
    "id",                   # Target node property
    "RESOURCE",             # Relationship label
    rel_direction_right=True,
) == expected_rels
```

---

## Error Messages Reference

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| `PropertyRef validation failed` | Missing type annotation or frozen=True | Check dataclass definition |
| `Node not found for relationship` | Target node doesn't exist | Load parent nodes first |
| `GraphJob failed` | Wrong common_job_parameters | Check UPDATE_TAG and tenant ID |
| `KeyError: 'field_name'` | Required field missing in API response | Use `.get()` for optional fields |
| `ModuleNotFoundError` | Missing `__init__.py` | Add `__init__.py` to all directories |
| `Relationship not created` | Matcher property mismatch | Verify property names match exactly |

---

## When to Ask for Help

Stop and ask the user if you encounter:

- Unclear business logic in legacy Cypher queries
- Complex relationships that don't map clearly to data model
- Test failures you can't resolve after multiple attempts
- Multiple modules that seem interdependent
- Performance issues that persist after adding indexes
- Unexpected data in the graph after sync
