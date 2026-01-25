# Enriching the Ontology

> **Related docs**: [Main AGENTS.md](../../AGENTS.md) | [Create Module](create-module.md) | [Add Node Type](add-node-type.md) | [Creating Security Rules](create-rule.md)

This guide covers how to integrate your module with Cartography's Ontology system to enable cross-module querying.

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

### Canonical Nodes (Legacy)

Creates separate abstract `User`/`Device` nodes:
- More complex - requires separate node creation and relationship management
- Additional storage overhead
- Useful when you need to aggregate data from multiple sources into single entities

## Step 1: Add Ontology Mapping Configuration

Create mapping configurations in `cartography/models/ontology/mapping/data/`:

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
            interative=False,
        ),
    ],
)
```

## Step 2: Add Ontology Configuration to Your Node Schema

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

## Step 3: Understanding Ontology Field Mappings

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

## Step 4: Handle Complex Relationships

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
        interative=False,
    ),
]
```

---

## Next Steps

For creating security rules that leverage the ontology system, see [Creating Security Rules](create-rule.md).
