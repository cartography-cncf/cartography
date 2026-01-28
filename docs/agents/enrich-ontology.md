# Enriching the Ontology

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Add Node Type](add-node-type.md)

This guide covers how to integrate your module with Cartography's Ontology system to enable cross-module querying.

## Table of Contents

1. [Overview of Ontology System](#overview-of-ontology-system)
2. [Types of Ontology Integration](#types-of-ontology-integration)
3. [Ontology Execution Flow](#ontology-execution-flow)
4. [Available Semantic Labels and Fields](#available-semantic-labels-and-fields)
5. [Step 1: Add Ontology Mapping Configuration](#step-1-add-ontology-mapping-configuration)
6. [Step 2: Register Your Mapping](#step-2-register-your-mapping)
7. [Step 3: Add Ontology Configuration to Your Node Schema](#step-3-add-ontology-configuration-to-your-node-schema)
8. [Step 4: Understanding Ontology Field Mappings](#step-4-understanding-ontology-field-mappings)
9. [Step 5: Handle Complex Relationships](#step-5-handle-complex-relationships)
10. [Testing Ontology Integration](#testing-ontology-integration)
11. [Documenting Ontology Integration](#documenting-ontology-integration)

## Overview of Ontology System

Cartography includes an **Ontology system** that provides both semantic labels and canonical nodes to unify data from multiple sources. This enables cross-module querying and provides a normalized view of identity and device management across your infrastructure.

The Ontology system works in two ways:
1. **Semantic Labels**: Adds semantic labels (like `UserAccount`) and prefixed properties (`_ont_*`) directly to source nodes for cross-module querying during ingestion
2. **Canonical Nodes**: Creates canonical nodes (like `(:User:Ontology)`) that represent unified entities

## Types of Ontology Integration

### Semantic Labels (Recommended)

Adds `UserAccount` labels and `_ont_*` properties to existing nodes:
- Simpler implementation - no additional node creation
- Direct querying of source nodes with normalized properties
- Automatic property mapping with special handling for data transformations
- Source tracking via `_ont_source` property

### Canonical Nodes

Creates separate abstract `User`/`Device` nodes:
- More complex - requires separate node creation and relationship management
- Additional storage overhead
- Useful when you need to aggregate data from multiple sources into single entities

## Ontology Execution Flow

Understanding when and how the ontology is applied:

### Semantic Labels (Applied at Ingestion Time)

Semantic labels are applied **automatically during data ingestion** when you call `load()`:

1. Your module calls `load(neo4j_session, YourSchema(), data, ...)`
2. Cartography checks if your schema has a semantic label (via `ExtraNodeLabels`)
3. If found, it looks up the mapping in `SEMANTIC_LABELS_MAPPING`
4. The `_ont_*` properties are automatically added to your nodes
5. The `_ont_source` property is set to track which module provided the data

### Canonical Nodes (Applied as Separate Intel Module)

Canonical nodes are created by a **dedicated intel module** (`cartography.intel.ontology`) that runs after your module:

1. Your module ingests data with semantic labels
2. The ontology intel module runs (configured via CLI options)
3. It reads source nodes from the graph matching the configured sources of truth
4. Creates `(:User:Ontology)` or `(:Device:Ontology)` canonical nodes
5. Executes `OntologyRelMapping` queries to link canonical nodes

**Configuration:**
```bash
# Configure sources of truth for ontology nodes
cartography --ontology-users-source "okta,entra,gsuite"
cartography --ontology-devices-source "crowdstrike,kandji,duo"
```

## Available Semantic Labels and Fields

For the complete list of available semantic labels and their fields, see:
- **Schema documentation**: [Ontology Schema](../root/modules/ontology/schema.md)
- **Mapping source code**: `cartography/models/ontology/mapping/data/`

## Step 1: Add Ontology Mapping Configuration

Create mapping configurations in `cartography/models/ontology/mapping/data/`.

### Available `special_handling` Options

When mapping fields, you can use these special handling options to transform values:

| Value | Description | Extra Parameters |
|-------|-------------|------------------|
| `invert_boolean` | Inverts the boolean value (`true` → `false`) | None |
| `to_boolean` | Converts to boolean, treating non-null as `true` | None |
| `or_boolean` | Logical OR of multiple boolean fields | `extra={"fields": ["field1", "field2"]}` |
| `nor_boolean` | Logical NOR of multiple boolean fields | `extra={"fields": ["field1", "field2"]}` |
| `equal_boolean` | Returns `true` if field value matches any of the specified values | `extra={"values": ["active", "bypass"]}` |
| `static_value` | Sets a static value, ignoring `node_field` | `extra={"value": "dynamodb"}` |

**Examples:**
```python
# Invert a boolean (disabled → active)
OntologyFieldMapping(
    ontology_field="active",
    node_field="disabled",
    special_handling="invert_boolean",
)

# OR multiple fields (suspended OR archived → inactive)
OntologyFieldMapping(
    ontology_field="active",
    node_field="suspended",
    extra={"fields": ["archived"]},
    special_handling="nor_boolean",
)

# Match against allowed values
OntologyFieldMapping(
    ontology_field="active",
    node_field="status",
    extra={"values": ["active", "bypass"]},
    special_handling="equal_boolean",
)

# Set a static value for database type
OntologyFieldMapping(
    ontology_field="type",
    node_field="",
    special_handling="static_value",
    extra={"value": "dynamodb"},
)
```

### For Semantic Labels

```python
# cartography/models/ontology/mapping/data/useraccounts.py
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping

# Add your mapping to the file
your_service_mapping = OntologyMapping(
    module_name="your_service",
    nodes=[
        OntologyNodeMapping(
            node_label="YourServiceUser",  # Your node label
            fields=[
                # Map your node fields to ontology fields with special handling
                OntologyFieldMapping(ontology_field="email", node_field="email"),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
                OntologyFieldMapping(ontology_field="fullname", node_field="display_name"),
                OntologyFieldMapping(ontology_field="firstname", node_field="first_name"),
                OntologyFieldMapping(ontology_field="lastname", node_field="last_name"),
                # Special handling examples:
                OntologyFieldMapping(
                    ontology_field="inactive",
                    node_field="account_enabled",
                    special_handling="invert_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="has_mfa",
                    node_field="multifactor",
                    special_handling="to_boolean",
                ),
                OntologyFieldMapping(
                    ontology_field="inactive",
                    node_field="suspended",
                    special_handling="or_boolean",
                    extra={"fields": ["archived"]},
                ),
            ],
        ),
    ],
)
```

### For Canonical Nodes

```python
# cartography/models/ontology/mapping/data/devices.py
from cartography.models.ontology.mapping.specs import OntologyFieldMapping
from cartography.models.ontology.mapping.specs import OntologyMapping
from cartography.models.ontology.mapping.specs import OntologyNodeMapping
from cartography.models.ontology.mapping.specs import OntologyRelMapping

# Add your mapping to the file
your_service_mapping = OntologyMapping(
    module_name="your_service",
    nodes=[
        OntologyNodeMapping(
            node_label="YourServiceDevice",  # Your node label
            fields=[
                # Map your node fields to ontology fields
                OntologyFieldMapping(ontology_field="hostname", node_field="device_name", required=True),  # Required field
                OntologyFieldMapping(ontology_field="os", node_field="operating_system"),
                OntologyFieldMapping(ontology_field="os_version", node_field="os_version"),
                OntologyFieldMapping(ontology_field="model", node_field="device_model"),
                OntologyFieldMapping(ontology_field="platform", node_field="platform"),
                OntologyFieldMapping(ontology_field="serial_number", node_field="serial"),
            ],
        ),
    ],
    # Optional: Add relationship mappings to connect Users to Devices
    rels=[
        OntologyRelMapping(
            __comment__="Link Device to User based on YourServiceUser-YourServiceDevice ownership",
            query="""
                MATCH (u:User)-[:HAS_ACCOUNT]->(:YourServiceUser)-[:OWNS]->(:YourServiceDevice)<-[:OBSERVED_AS]-(d:Device)
                MERGE (u)-[r:OWNS]->(d)
                ON CREATE SET r.firstseen = timestamp()
                SET r.lastupdated = $UPDATE_TAG
            """,
            iterative=False,
        ),
    ],
)
```

## Step 2: Register Your Mapping

After creating your mapping, you must register it so Cartography can discover it.

1. Add your mapping to the appropriate file in `cartography/models/ontology/mapping/data/`

2. Add your mapping to the dictionary at the bottom of the file:

```python
# Example: At the bottom of useraccounts.py
USERACCOUNTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    # ... existing mappings ...
    "your_service": your_service_mapping,  # Add your mapping here
}
```

The mappings are automatically imported via `cartography/models/ontology/mapping/__init__.py`.

## Step 3: Add Ontology Configuration to Your Node Schema

### Semantic Labels

Simply add the semantic label - the ontology system will automatically add `_ont_*` properties at the ingestion time.

```python
from cartography.models.core.nodes import ExtraNodeLabels

@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    # Add UserAccount label for semantic ontology integration
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
```

That's it! The ontology system will automatically:
- Add `_ont_email`, `_ont_fullname`, etc. properties to your nodes
- Apply any special handling (boolean conversion, inversion, etc.)
- Add `_ont_source` property to track which module provided the data

### Canonical Nodes

You need to define a Schema model for the canonical node and add a relationship to it (similar to regular intel nodes)

```python
@dataclass(frozen=True)
class UserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("email")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    fullname: PropertyRef = PropertyRef("fullname")
    firstname: PropertyRef = PropertyRef("firstname")
    lastname: PropertyRef = PropertyRef("lastname")
    inactive: PropertyRef = PropertyRef("inactive")


@dataclass(frozen=True)
class UserToUserAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# (:User)-[:HAS_ACCOUNT]->(:UserAccount)
# This is a relationship to a sementic label used by modules' users nodes
@dataclass(frozen=True)
class UserToUserAccountRel(CartographyRelSchema):
    target_node_label: str = "UserAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"email": PropertyRef("email")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ACCOUNT"
    properties: UserToUserAccountRelProperties = UserToUserAccountRelProperties()


@dataclass(frozen=True)
class UserSchema(CartographyNodeSchema):
    label: str = "User"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Ontology"])
    properties: UserNodeProperties = UserNodeProperties()
    scoped_cleanup: bool = False
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[UserToUserAccountRel()],
    )
```

## Step 4: Understanding Ontology Field Mappings

### Required Fields

The `required` parameter in `OntologyFieldMapping` serves two critical purposes:

**1. Data Quality Control**: When `required=True`, source nodes that lack this field (i.e., the field is `None` or missing) will be completely excluded from ontology node creation. This ensures only complete, usable data creates ontology nodes.

**2. Primary Identifier Validation**: Fields used as primary identifiers **must** be marked as required to ensure ontology nodes can always be properly identified and matched across data sources.

```python
# DO: Mark primary identifiers as required
OntologyFieldMapping(ontology_field="email", node_field="email", required=True),        # Users
OntologyFieldMapping(ontology_field="hostname", node_field="device_name", required=True), # Devices

# DO: Mark optional fields as not required (default)
OntologyFieldMapping(ontology_field="firstname", node_field="first_name"),  # Optional field
```

**Example**: If a `DuoUser` node has no email address and email is marked as `required=True`, no corresponding `User` ontology node will be created for that record.

### Node Eligibility

The `eligible_for_source` parameter in `OntologyNodeMapping` controls whether this node mapping can create new ontology nodes (default: `True`).

**When to set `eligible_for_source=False`:**
- Node type lacks sufficient data to create meaningful ontology nodes (e.g., no email for Users)
- Node serves only as a connection point to existing ontology nodes
- Required fields are not available or reliable enough for primary node creation

```python
# Example: AWS IAM users don't have email addresses (required for User ontology nodes)
OntologyNodeMapping(
    node_label="AWSUser",
    eligible_for_source=False,  # Cannot create new User ontology nodes
    fields=[
        OntologyFieldMapping(ontology_field="username", node_field="name")
    ],
),
```

In this example, AWS IAM users can be linked to existing User ontology nodes through relationships, but they cannot create new User nodes since they lack email addresses.

## Step 5: Handle Complex Relationships

For services that have user-device relationships, add relationship mappings:

```python
# In your device mapping
rels=[
    OntologyRelMapping(
        __comment__="Connect users to their devices",
        query="""
            MATCH (u:User)-[:HAS_ACCOUNT]->(:YourServiceUser)-[:OWNS]->(:YourServiceDevice)<-[:OBSERVED_AS]-(d:Device)
            MERGE (u)-[r:OWNS]->(d)
            ON CREATE SET r.firstseen = timestamp()
            SET r.lastupdated = $UPDATE_TAG
        """,
        iterative=False,
    ),
]
```

## Testing Ontology Integration

To verify your ontology integration works correctly:

### For Semantic Labels

Check that `_ont_*` properties are added to your nodes:

```python
def test_ontology_properties(neo4j_session):
    # After running your sync function
    result = neo4j_session.run(
        "MATCH (n:YourServiceUser) RETURN n._ont_email, n._ont_source LIMIT 1"
    ).single()

    assert result["n._ont_email"] is not None
    assert result["n._ont_source"] == "your_service"
```

### For Canonical Nodes

Check that canonical nodes and relationships are created:

```python
def test_canonical_user_created(neo4j_session):
    # After running the ontology intel module
    result = neo4j_session.run(
        """
        MATCH (u:User:Ontology)-[:HAS_ACCOUNT]->(ua:YourServiceUser)
        RETURN count(u) as user_count
        """
    ).single()

    assert result["user_count"] > 0
```

## Documenting Ontology Integration

When your node has an ontology integration (semantic label or canonical node relationship), you must document it in the schema file (`docs/root/modules/your_service/schema.md`).

### Standard Ontology Mapping Phrase

Add a blockquote immediately after the node description using this format:

```markdown
### YourServiceUser

Represents a user in Your Service.

> **Ontology Mapping**: This node has the extra label `{SemanticLabel}` to enable cross-platform queries for {description} across different systems (e.g., {examples}).
```

### Phrase Templates by Semantic Label

| Semantic Label | Standard Phrase |
|----------------|-----------------|
| `UserAccount` | `> **Ontology Mapping**: This node has the extra label \`UserAccount\` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GSuiteUser).` |
| `DeviceInstance` | `> **Ontology Mapping**: This node has the extra label \`DeviceInstance\` to enable cross-platform queries for device instances across different systems (e.g., CrowdStrikeDevice, KandjiDevice, JamfComputer).` |
| `Tenant` | `> **Ontology Mapping**: This node has the extra label \`Tenant\` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).` |
| `Database` | `> **Ontology Mapping**: This node has the extra label \`Database\` to enable cross-platform queries for databases across different systems (e.g., RDSInstance, DynamoDBTable, BigQueryDataset).` |

### Example: AWSAccount with Tenant Label

From `docs/root/modules/aws/schema.md`:

```markdown
### AWSAccount

Representation of an AWS Account.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).

| Field | Description |
|-------|-------------|
| firstseen | Timestamp of when a sync job discovered this node |
| name | The name of the account |
| lastupdated | Timestamp of the last time the node was updated |
| **id** | The AWS Account ID number |
```
