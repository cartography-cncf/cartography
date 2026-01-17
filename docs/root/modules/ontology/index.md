# Ontology in Cartography

## What is an Ontology?

An ontology is a structured representation of concepts and relationships within a given domain. It enables semantic modeling of knowledge, making it easier to organize, analyze, and query data. In Cartography, the ontology defines entity (node) types and their relationships, using semantic labels and abstract nodes for better interoperability and extensibility.

A key benefit of this approach is that it enables cross-module queries and the export of data in a unified format. By providing a common semantic layer, different modules can interact seamlessly, and data from various sources can be normalized and exported consistently.

### Implementation in Cartography

Cartography implements ontology using two main concepts:
- **Semantic Label**: Each graph node can have one or more semantic labels describing its nature (e.g., `UserAccount`, `DNSRecord`).
- **Abstract Nodes**: Some nodes serve as abstract concepts to group similar entities or define common behaviors. This allows logic to be factored and ensures model consistency.

:::{seealso}
For more background and design rationale, see:
- [Unifying the Graph: Why We Introduced an Ontology in Cartography](https://medium.com/@jychp/unifying-the-graph-why-we-introduced-an-ontology-in-cartography-33b9301de22d)
- [RFC: Cartography Ontology Schema](https://github.com/cartography-cncf/cartography/discussions/1579)
:::

## How Ontology Works in Cartography

The `intel.ontology` module in Cartography manages ontology logic. It allows:
- Loading ontology definitions from JSON files
- Validating the consistency of entities and relationships
- Ensuring mapping between collected data and the defined semantic model

The module provides functions to traverse, enrich, and leverage the ontology during data ingestion. It plays a key role in normalizing entities from heterogeneous sources.

By default, nodes are created in the ontology based on data observed in various modules. For some node, such as User, Device, etc., you can specify "sources of truth" modules that will exclusively create those nodes. This allows for more controlled and accurate representation of certain entities.

**Example: User Nodes and Source of Truth**

If you set the `--ontology-users-source` parameter to `duo`, then a `User` node will be created for every account found in Duo. In contrast, for other integrations like Tailscale, only existing `User` nodes (those created by the source of truth) will be linked to Tailscale accounts. No new `User` nodes will be created from Tailscale data alone.

## Ontology Field Mappings

Ontology mappings are defined in Python using the `OntologyFieldMapping` class, which maps fields from source nodes to ontology nodes. Each mapping specifies:

- `ontology_field`: The field name in the ontology node (e.g., "email", "hostname")
- `node_field`: The corresponding field name in the source node (e.g., "email_address", "device_name")
- `required`: Whether this field is required for ontology node creation (defaults to `False`)

**Example:**
```python
OntologyFieldMapping(
    ontology_field="email",
    node_field="email_address",
    required=True
)
```

### Required Fields

The `required` flag serves two critical purposes:

1. **Data Quality Control**: If a source node lacks a required field (i.e., the field is `None` or missing), the entire ontology node creation is skipped for that record. This ensures only complete, usable data creates ontology nodes.

2. **Primary Identifier Validation**: Fields that serve as primary identifiers must be marked as required. For example:
   - `email` should be required for User ontology nodes
   - `hostname` should be required for Device ontology nodes

This prevents creating ontology nodes that cannot be properly identified or matched across different data sources.

**Example with Required Field:**
```python
# If a source DuoUser has no email, no User ontology node is created
OntologyFieldMapping(ontology_field="email", node_field="email", required=True)
```

### Special Field Handling

Ontology field mappings support special handling for complex data transformations using the `special_handling` parameter:

#### `invert_boolean`
Inverts boolean values - useful when a source field represents the opposite of the ontology field:
```python
OntologyFieldMapping(
    ontology_field="inactive",
    node_field="account_enabled",
    special_handling="invert_boolean",
)
# account_enabled=True becomes inactive=False
```

#### `to_boolean`
Converts any non-null value to `True`, null/missing values to `False`:
```python
OntologyFieldMapping(
    ontology_field="has_mfa",
    node_field="multifactor",
    special_handling="to_boolean",
)
# Any non-null multifactor value becomes has_mfa=True
```

#### `or_boolean`
Combines multiple boolean fields using logical OR - useful when a concept spans multiple source fields:
```python
OntologyFieldMapping(
    ontology_field="inactive",
    node_field="suspended",
    special_handling="or_boolean",
    extra={"fields": ["archived"]},
)
# inactive = suspended OR archived
```

#### `equal_boolean`
Checks if the field value equals any of the specified values:
```python
OntologyFieldMapping(
    ontology_field="inactive",
    node_field="status",
    special_handling="equal_boolean",
    extra={"values": ["disabled", "locked out", "pending deletion"]},
)
# inactive=True if status is "disabled", "locked out", or "pending deletion"
```

### Node Eligibility

The `eligible_for_source` parameter in `OntologyNodeMapping` controls whether a node mapping can create new ontology nodes (default: `True`).

Set `eligible_for_source=False` when:
- A node type lacks sufficient data to create meaningful ontology nodes
- The node serves only as a connection point to existing ontology nodes
- Required fields are not available or reliable enough for primary node creation

**Example:**
```python
OntologyNodeMapping(
    node_label="AWSUser",
    eligible_for_source=False,  # Cannot create User ontology nodes
    fields=[
        OntologyFieldMapping(ontology_field="username", node_field="name")
    ],
)
```

In this example, AWS IAM users don't have email addresses (required for User ontology nodes), so they're marked as ineligible for creating new User nodes. They can still be linked to existing User nodes through relationships.

## Ontology Mapping Structure

Ontology mappings are defined in `cartography/models/ontology/mapping/data/` using Python dataclasses:

```python
your_service_mapping = OntologyMapping(
    module_name="your_service",
    nodes=[
        OntologyNodeMapping(
            node_label="YourServiceUser",
            fields=[
                OntologyFieldMapping(ontology_field="email", node_field="email", required=True),
                OntologyFieldMapping(ontology_field="username", node_field="username"),
                OntologyFieldMapping(ontology_field="fullname", node_field="display_name"),
            ],
        ),
    ],
    rels=[
        OntologyRelMapping(
            __comment__="Link User to Device based on observed relationships",
            query="MATCH (u:User)-[:HAS_ACCOUNT]->(:YourServiceUser)-[:OWNS]->(:YourServiceDevice)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
            iterative=False,
        ),
    ],
)
```

This structure allows Cartography to flexibly describe how to map and relate entities from specific integrations into the unified ontology graph.

```{toctree}
config
schema
```
