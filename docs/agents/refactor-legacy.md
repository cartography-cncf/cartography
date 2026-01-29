# Refactoring Legacy Code to Data Model

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Add Node Type](add-node-type.md)

**IMPORTANT**: A critical task for AI agents is refactoring legacy Cartography code from handwritten Cypher queries to the modern data model approach. This guide provides a step-by-step procedure to safely perform these refactors.

## Overview

Legacy Cartography modules use handwritten Cypher queries to create nodes and relationships. The modern approach uses declarative data models that automatically generate optimized queries. Refactoring improves maintainability, performance, and consistency.

## Step 1: Prevent Regressions (CRITICAL)

**Before touching any code**, ensure you have comprehensive test coverage:

### 1a. Identify the Sync Function
- Locate the main `sync_*()` function for the module
- This is usually named like `sync_ec2_instances()`, `sync_users()`, etc.
- Example: `cartography.intel.aws.ec2.instances.sync()`

### 1b. Ensure Integration Test Exists
- Check for integration tests in `tests/integration/cartography/intel/[module]/`
- The test MUST call the sync function directly
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

## Step 2: Convert to Data Model

Now safely convert the legacy code to use the modern data model:

### 2a. Create Data Model Schema Files

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

### 2b. Replace load_* Functions

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

### 2c. Replace cleanup_* Functions

Replace handwritten cleanup with data model cleanup:

```python
# Before (legacy)
def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    run_cleanup_job('aws_import_ec2_instances_cleanup.json', neo4j_session, common_job_parameters)

# After (data model)
def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(EC2InstanceSchema(), common_job_parameters).run(neo4j_session)
```

### 2d. Test Continuously
- Run your integration test after each change
- Ensure it still passes - if not, debug before continuing
- You may need to update minor details in tests due to data model differences

## Step 3: Cleanup Legacy Files

Once tests pass, clean up legacy infrastructure:

### 3a. Remove Index Entries

Remove manual index entries from `cartography/data/indexes.cypher`:

```cypher
# Remove entries like these - data model creates indexes automatically
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.lastupdated);
```

**Note**: Only remove indexes for nodes you've converted to data model. Leave others untouched.

### 3b. Remove Cleanup Job Files

Remove corresponding cleanup JSON files from `cartography/data/jobs/cleanup/`:

```bash
# Remove files like:
rm cartography/data/jobs/cleanup/aws_import_ec2_instances_cleanup.json
```

**Note**: Only remove cleanup files for modules you've fully converted.

## Common Refactoring Patterns

### Pattern 1: Simple Node Migration

Most legacy nodes can be directly converted to data model schemas.

### Pattern 2: Complex Relationships

For modules with complex relationships, you may need:
- **One-to-Many relationships** (see [Add Node Type](add-node-type.md))
- **Composite Node Pattern** for nodes that get data from multiple sources

### Pattern 3: MatchLinks for Complex Cases

Use [MatchLinks](add-relationship.md#matchlinks-connecting-existing-nodes) sparingly, only when:
- Connecting two existing node types from separate data sources
- Rich relationship properties that don't belong in nodes

## Things You May Encounter

### Multiple Intel Modules Modifying Same Nodes

When refactoring modules that modify the same node type:
- Use **Simple Relationship Pattern** if only referencing by ID
- Use **Composite Node Pattern** for different views of the same entity from different data sources (see [Add Relationship](add-relationship.md#multiple-intel-modules-modifying-the-same-node-type))

### Legacy Test Adjustments

Older tests may need small tweaks:
- Update expected property names if data model changes them
- Adjust relationship directions if needed
- Remove tests for manual cleanup jobs (data model handles this)

### Complex Cypher Queries

Some legacy queries are complex. Break them down:
1. Identify what nodes/relationships are being created
2. Map to data model schemas
3. Use multiple `load()` calls if needed

## What NOT to Test

**Do NOT explicitly test cleanup functions** unless there's a specific concern:
- Data model handles complex cleanup cases automatically
- Testing cleanup adds unnecessary boilerplate
- Focus tests on data ingestion, not cleanup behavior

## When to Stop and Ask

Refactors can be complex. **Stop and ask the user** if you encounter:
- Unclear business logic in legacy Cypher
- Complex relationships that don't map clearly to data model
- Test failures you can't resolve
- Multiple modules that seem interdependent

## Refactoring Checklist

Before submitting a refactor:

- [ ] **Integration test exists and passes** for the sync function
- [ ] **Data model schemas** defined with proper relationships
- [ ] **Legacy load functions** converted to use `load()`
- [ ] **Legacy cleanup functions** converted to use `GraphJob.from_node_schema()`
- [ ] **Tests still pass** after all changes
- [ ] **Index entries removed** from `indexes.cypher`
- [ ] **Cleanup JSON files removed** from cleanup directory
- [ ] **No regressions** - all functionality preserved

## Success Criteria

A successful refactor should:
1. **Preserve all functionality** - tests pass
2. **Use data model** - no handwritten Cypher for CRUD operations
3. **Clean up legacy files** - indexes and cleanup jobs removed
4. **Maintain performance** - no significant speed degradation
5. **Follow patterns** - consistent with other modern modules
