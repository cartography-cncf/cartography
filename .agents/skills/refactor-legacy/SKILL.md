---
name: refactor-legacy
description: Convert a legacy handwritten-Cypher Cartography sync (`load_*` / `cleanup_*` JSON jobs) into the modern declarative data model (`load()`, `GraphJob.from_node_schema()`). Use when the user asks to refactor, modernise, migrate, or "clean up" a legacy intel module, or to remove a `cleanup/*.json` job tied to an old `MERGE` query.
---

# refactor-legacy

A critical task for AI agents: refactor legacy Cartography modules from handwritten Cypher to the declarative data model. The modern approach generates optimised queries automatically, improves maintainability, and removes manual index / cleanup boilerplate.

## Critical rules

1. **Test coverage first.** Do **not** touch production code until an integration test exists and passes against the **legacy** code. If no test exists, write one and confirm it passes before refactoring.
2. **Convert `MERGE`/`CREATE` write queries to `load()`** with `CartographyNodeSchema`. Convert handwritten cleanup to `GraphJob.from_node_schema()`.
3. **If a hand-written write must remain temporarily**, switch it to `run_write_query()` (managed transaction + retries). Never keep raw `neo4j_session.run(...)` writes during refactors.
4. **Only delete legacy artefacts for the nodes you actually converted** — leave indexes and cleanup JSON for unconverted nodes alone.
5. **Re-run the integration test after every chunk** of conversion. If it fails, debug before continuing — do not pile on more changes.
6. **Stop and ask the user** when business logic in legacy Cypher is unclear, when relationships don't map cleanly, when tests fail repeatedly, or when modules look interdependent.

## Instructions

### Step 1 — Prevent regressions (CRITICAL)

#### 1a. Identify the sync function

Locate the main `sync_*()` for the module — usually `sync_ec2_instances()`, `sync_users()`, etc.

Example: `cartography.intel.aws.ec2.instances.sync()`.

#### 1b. Ensure an integration test exists

Look in `tests/integration/cartography/intel/[module]/`. The test **must** call the sync function directly. If none exists, create one **before any refactoring**:

```python
# tests/integration/cartography/intel/aws/ec2/test_instances.py
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
from tests.data.aws.ec2.instances import MOCK_INSTANCES_DATA
from tests.integration.util import check_nodes, check_rels


TEST_UPDATE_TAG = 123456789
TEST_AWS_ACCOUNT_ID = "123456789012"


@patch.object(cartography.intel.aws.ec2.instances, "get", return_value=MOCK_INSTANCES_DATA)
def test_sync_ec2_instances(mock_get, neo4j_session):
    cartography.intel.aws.ec2.instances.sync(
        neo4j_session,
        boto3_session=None,  # mocked
        regions=["us-east-1"],
        current_aws_account_id=TEST_AWS_ACCOUNT_ID,
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters={
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AWS_ID": TEST_AWS_ACCOUNT_ID,
        },
    )

    expected_nodes = {
        ("i-1234567890abcdef0", "running"),
        ("i-0987654321fedcba0", "stopped"),
    }
    assert check_nodes(neo4j_session, "EC2Instance", ["id", "state"]) == expected_nodes
```

Run the test against the legacy code and ensure it passes. If it does not exist or does not pass, fix that first — **no exceptions**.

### Step 2 — Convert to the data model

#### 2a. Create schemas in `cartography/models/[module]/`

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

For node, relationship, and schema details, see the `add-node-type` and `add-relationship` skills.

#### 2b. Replace `load_*` functions

```python
# Before
def load_ec2_instances(neo4j_session, data, region, current_aws_account_id, update_tag):
    ingest_instances = """
    UNWIND $instances_list AS instance
    MERGE (i:EC2Instance {id: instance.id})
    ON CREATE SET i.firstseen = timestamp()
    SET i.instanceid = instance.InstanceId,
        i.state = instance.State,
        i.lastupdated = $update_tag
    WITH i
    MATCH (owner:AWSAccount {id: $aws_account_id})
    MERGE (owner)-[r:RESOURCE]->(i)
    ON CREATE SET r.firstseen = timestamp()
    SET r.lastupdated = $update_tag
    """
    neo4j_session.run(ingest_instances, instances_list=data, aws_account_id=current_aws_account_id, update_tag=update_tag)


# After
def load_ec2_instances(neo4j_session, data, region, current_aws_account_id, update_tag):
    load(
        neo4j_session,
        EC2InstanceSchema(),
        data,
        lastupdated=update_tag,
        AWS_ID=current_aws_account_id,
    )
```

If you genuinely need a hand-written write query during the refactor, replace `neo4j_session.run(...)` with `run_write_query()` so the write benefits from Cartography's managed transaction + retry handling.

#### 2c. Replace `cleanup_*` functions

```python
# Before
def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    run_cleanup_job("aws_import_ec2_instances_cleanup.json", neo4j_session, common_job_parameters)


# After
def cleanup_ec2_instances(neo4j_session, common_job_parameters):
    GraphJob.from_node_schema(EC2InstanceSchema(), common_job_parameters).run(neo4j_session)
```

#### 2d. Test continuously

After each chunk, run the integration test. Tests may need minor tweaks for property names that the data model normalises, but they should keep passing.

### Step 3 — Cleanup legacy artefacts

Once tests pass, remove the legacy bookkeeping for the nodes you converted.

#### 3a. Remove manual index entries

In `cartography/data/indexes.cypher`:

```cypher
# Remove entries like these — the data model creates indexes automatically
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.id);
CREATE INDEX IF NOT EXISTS FOR (n:EC2Instance) ON (n.lastupdated);
```

Only remove indexes for nodes you actually converted.

#### 3b. Remove cleanup job JSONs

```bash
rm cartography/data/jobs/cleanup/aws_import_ec2_instances_cleanup.json
```

Only remove cleanup files for fully-converted modules.

## Common refactoring patterns

- **Simple node migration.** Most legacy nodes map directly to a node schema.
- **Complex relationships.** May need one-to-many (`add-node-type` skill) or composite-node patterns (`add-relationship` skill).
- **MatchLinks.** Use sparingly — only for connecting two existing node types from separate data sources, or rich relationship metadata. See `add-relationship` skill.

## Things you may encounter

### Multiple intel modules modifying the same nodes

- Reference by ID only -> simple relationship pattern.
- Different views of the same entity from different sources -> composite node pattern.

(See `add-relationship` skill, "Multi-module patterns".)

### Legacy test adjustments

- Update expected property names if the data model changes them.
- Adjust relationship directions if needed.
- Remove tests for manual cleanup jobs (data model handles cleanup).

### Complex Cypher queries

Break them down: identify what nodes/relationships are being created, map to schemas, then use multiple `load()` calls if needed.

## What NOT to test

Do **not** explicitly test cleanup unless you have a specific concern. The data model handles complex cleanup automatically and testing it adds boilerplate. Focus tests on data ingestion outcomes.

## When to stop and ask

Refactors get hairy. Stop and ask the user when:

- Legacy Cypher contains business logic that isn't obvious.
- Relationships don't map cleanly to the data model.
- Tests fail repeatedly and you cannot resolve them.
- Multiple modules look interdependent.

## Refactoring checklist

- [ ] Integration test exists and passes against the legacy code
- [ ] Data model schemas defined with proper relationships
- [ ] Legacy `load_*` functions converted to `load()`
- [ ] Legacy `cleanup_*` functions converted to `GraphJob.from_node_schema()`
- [ ] Tests still pass after all changes
- [ ] Manual index entries removed from `indexes.cypher`
- [ ] Cleanup JSON files removed from `cartography/data/jobs/cleanup/`
- [ ] No regressions in functionality
- [ ] Commits signed (`git commit -s`)

## Success criteria

A successful refactor:

1. Preserves all functionality (tests pass).
2. Uses the data model (no handwritten Cypher for CRUD).
3. Cleans up legacy artefacts (indexes + cleanup JSONs removed).
4. Maintains performance (no significant degradation).
5. Follows the modern-module patterns consistently.

## Common issues

See the `troubleshooting` skill for `PropertyRef validation failed`, missing relationships, cleanup misbehaviour, and related errors.
