---
name: enrich-ontology
description: Map a Cartography node into the Ontology system using semantic labels (UserAccount, DeviceInstance, Tenant, Database, ObjectStorage, FileStorage) or canonical nodes (User, Device). Use when the user asks to add ontology mapping, expose a node as a semantic label, normalise identity / device data across providers, enable cross-module queries, or wire `_ont_*` properties.
---

# enrich-ontology

Cartography's Ontology system unifies data from multiple sources via two mechanisms:

1. **Semantic labels (recommended)** — adds labels (e.g. `UserAccount`) and prefixed properties (`_ont_*`) directly to source nodes during ingestion.
2. **Canonical nodes** — separate `(:User:Ontology)` / `(:Device:Ontology)` nodes that aggregate data from multiple sources.

Most modules only need semantic labels.

## Critical rules

1. **Mark primary identifiers `required=True`** in `OntologyFieldMapping` (e.g. `email` for `User`, `hostname` for `Device`). Records missing these are excluded from ontology node creation.
2. **For semantic labels, just add `ExtraNodeLabels(["UserAccount"])`** to your node schema. The ontology system handles the `_ont_*` properties automatically.
3. **`special_handling` values are strings**: `invert_boolean`, `to_boolean`, `or_boolean`, `nor_boolean`, `equal_boolean`, `static_value`. Boolean conditions inside `extra={"values": ...}` must also be strings (`"true"`, not `True`).
4. **Document ontology mapping** in your schema doc using the standard blockquote phrase.
5. **Module name `microsoft`** is the canonical source for Microsoft Graph. `entra` is still accepted as a backward-compatible alias during migration.

## Instructions

### Step 1 — Decide: semantic label or canonical node?

| Need                                                                                  | Use                |
| ------------------------------------------------------------------------------------- | ------------------ |
| Cross-module queries on existing source nodes (e.g. all `UserAccount` across systems) | Semantic label     |
| Aggregate one entity from many sources into a single canonical record                 | Canonical node     |

When in doubt, start with semantic label.

### Step 2 — Author the mapping

Add the mapping in `cartography/models/ontology/mapping/data/`. For users:

```python
# cartography/models/ontology/mapping/data/useraccounts.py
from cartography.models.ontology.mapping.specs import (
    OntologyFieldMapping, OntologyMapping, OntologyNodeMapping,
)


your_service_mapping = OntologyMapping(
    module_name="your_service",
    nodes=[
        OntologyNodeMapping(
            node_label="YourServiceUser",
            fields=[
                OntologyFieldMapping(ontology_field="email",     node_field="email", required=True),
                OntologyFieldMapping(ontology_field="username",  node_field="username"),
                OntologyFieldMapping(ontology_field="fullname",  node_field="display_name"),
                OntologyFieldMapping(ontology_field="firstname", node_field="first_name"),
                OntologyFieldMapping(ontology_field="lastname",  node_field="last_name"),

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

For devices the pattern is the same with `OntologyNodeMapping(node_label="YourServiceDevice", ...)`.

### Step 3 — Register the mapping

Add it to the dictionary at the bottom of the file:

```python
# Example: bottom of useraccounts.py
USERACCOUNTS_ONTOLOGY_MAPPING: dict[str, OntologyMapping] = {
    # ... existing mappings ...
    "your_service": your_service_mapping,
}
```

The mappings are auto-imported via `cartography/models/ontology/mapping/__init__.py`.

### Step 4 — Wire the semantic label on your node schema

For semantic labels, the node schema simply gains the extra label — Cartography injects `_ont_*` and `_ont_source` automatically at ingestion:

```python
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class YourServiceUserSchema(CartographyNodeSchema):
    label: str = "YourServiceUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: YourServiceUserNodeProperties = YourServiceUserNodeProperties()
    sub_resource_relationship: YourServiceTenantToUserRel = YourServiceTenantToUserRel()
```

For canonical nodes, define a separate schema with `extra_node_labels=ExtraNodeLabels(["Ontology"])` and a relationship to the semantic-labelled source nodes. See `references/semantic-labels.md` for the full template.

### Step 5 — `required` and `eligible_for_source`

`required=True` means: source records lacking this field are **excluded** from ontology node creation. Always mark the primary identifier required:

```python
OntologyFieldMapping(ontology_field="email",    node_field="email",       required=True)
OntologyFieldMapping(ontology_field="hostname", node_field="device_name", required=True)
```

`OntologyNodeMapping.eligible_for_source=False` means: this mapping links existing ontology nodes but cannot **create** new ones. Use it when the source lacks the required identifier:

```python
# AWS IAM users have no email, so they cannot create new User ontology nodes.
OntologyNodeMapping(
    node_label="AWSUser",
    eligible_for_source=False,
    fields=[
        OntologyFieldMapping(ontology_field="username", node_field="name"),
    ],
),
```

### Step 6 — Cross-entity relationships (e.g. user owns device)

For services that link users to devices, add a statement to the appropriate ontology analysis JSON file (e.g. `cartography/data/jobs/analysis/ontology_devices_linking.json`):

```json
{
  "__comment": "Connect users to their devices via YourService",
  "query": "MATCH (u:User)-[:HAS_ACCOUNT]->(:YourServiceUser)-[:OWNS]->(:YourServiceDevice)<-[:OBSERVED_AS]-(d:Device) MERGE (u)-[r:OWNS]->(d) ON CREATE SET r.firstseen = timestamp() SET r.lastupdated = $UPDATE_TAG",
  "iterative": false
}
```

See the `analysis-jobs` skill for the JSON job format.

### Step 7 — Test

For semantic labels — assert `_ont_*` properties land on your nodes:

```python
def test_ontology_properties(neo4j_session):
    # after running your sync
    row = neo4j_session.run(
        "MATCH (n:YourServiceUser) RETURN n._ont_email, n._ont_source LIMIT 1"
    ).single()
    assert row["n._ont_email"] is not None
    assert row["n._ont_source"] == "your_service"
```

For canonical nodes — assert the ontology intel module produces them:

```python
def test_canonical_user_created(neo4j_session):
    row = neo4j_session.run(
        """
        MATCH (u:User:Ontology)-[:HAS_ACCOUNT]->(ua:YourServiceUser)
        RETURN count(u) AS user_count
        """
    ).single()
    assert row["user_count"] > 0
```

### Step 8 — Document the integration

In `docs/root/modules/your_service/schema.md`, add the standard blockquote phrase under the node title:

```markdown
### YourServiceUser

Represents a user in Your Service.

> **Ontology Mapping**: This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GSuiteUser).
```

Standard phrases by semantic label:

| Semantic label    | Standard phrase                                                                                                                                                                          |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UserAccount`     | This node has the extra label `UserAccount` to enable cross-platform queries for user accounts across different systems (e.g., OktaUser, EntraUser, GSuiteUser).                         |
| `DeviceInstance`  | This node has the extra label `DeviceInstance` to enable cross-platform queries for device instances across different systems (e.g., CrowdStrikeDevice, KandjiDevice, JamfComputer).     |
| `Tenant`          | This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).      |
| `Database`        | This node has the extra label `Database` to enable cross-platform queries for databases across different systems (e.g., RDSInstance, DynamoDBTable, BigQueryDataset).                    |
| `ObjectStorage`   | This node has the extra label `ObjectStorage` to enable cross-platform queries for object storage across different systems (e.g., S3Bucket, GCPBucket, AzureStorageBlobContainer).       |
| `FileStorage`     | This node has the extra label `FileStorage` to enable cross-platform queries for network file systems and shares across different systems (e.g., EfsFileSystem, AzureStorageFileShare).  |

## `special_handling` quick reference

| Value             | Description                                                | Extra params                              |
| ----------------- | ---------------------------------------------------------- | ----------------------------------------- |
| `invert_boolean`  | Inverts the boolean value (`true` -> `false`)              | None                                      |
| `to_boolean`      | Converts to boolean, treating non-null as `true`           | None                                      |
| `or_boolean`      | Logical OR over multiple boolean fields                    | `extra={"fields": [...]}`                 |
| `nor_boolean`     | Logical NOR over multiple boolean fields                   | `extra={"fields": [...]}`                 |
| `equal_boolean`   | `true` if value matches any of the specified strings       | `extra={"values": ["active", "bypass"]}`  |
| `static_value`    | Sets a static value, ignoring `node_field`                 | `extra={"value": "dynamodb"}`             |

## Canonical node configuration (CLI)

```bash
cartography --ontology-users-source "okta,microsoft,gsuite"
cartography --ontology-devices-source "crowdstrike,kandji,duo"
```

## References (load on demand)

- `references/semantic-labels.md` — execution flow, available labels/fields, full canonical-node schema example, `eligible_for_source` deep dive.
