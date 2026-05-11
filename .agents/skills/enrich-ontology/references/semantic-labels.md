# Semantic labels and canonical nodes: deep dive

## Contents

- Execution flow
- Available semantic labels and fields
- Canonical node schema template
- `required` vs `eligible_for_source`
- Documenting ontology integration in schema docs

## Execution flow

### Semantic labels — applied at ingestion

Applied automatically when you call `load()`:

1. Module calls `load(neo4j_session, YourSchema(), data, ...)`.
2. Cartography checks if the schema has a semantic label (via `ExtraNodeLabels`).
3. If found, looks up the mapping in `SEMANTIC_LABELS_MAPPING`.
4. `_ont_*` properties are added automatically.
5. `_ont_source` is set to the module name.

### Canonical nodes — applied as a separate intel module

Created by the dedicated `cartography.intel.ontology` intel module that runs after your module:

1. Your module ingests data with semantic labels.
2. The ontology intel module runs (configured via CLI options).
3. It reads source nodes matching the configured sources of truth.
4. Creates `(:User:Ontology)` or `(:Device:Ontology)` canonical nodes.
5. Runs ontology analysis jobs to link canonical nodes.

```bash
cartography --ontology-users-source "okta,microsoft,gsuite"
cartography --ontology-devices-source "crowdstrike,kandji,duo"
```

`microsoft` is the canonical source name for Microsoft Graph data. `entra` is still accepted as a backward-compatible alias during the migration.

## Available semantic labels and fields

For the complete list, see:

- Schema docs: `docs/root/modules/ontology/schema.md`.
- Mapping source code: `cartography/models/ontology/mapping/data/`.

## Canonical node schema template

When you opt into canonical nodes, define the schema and the relationship between canonical and source nodes:

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
# Links the canonical User to the semantic UserAccount on source nodes.
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

## `required` vs `eligible_for_source`

### `required=True`

Two purposes:

1. **Data quality** — source nodes lacking this field (`None` / missing) are excluded entirely from ontology node creation.
2. **Primary identifier validation** — fields used as primary identifiers **must** be required so ontology nodes can be matched across data sources.

```python
# DO — primary identifiers
OntologyFieldMapping(ontology_field="email",    node_field="email",       required=True)  # users
OntologyFieldMapping(ontology_field="hostname", node_field="device_name", required=True)  # devices

# DO — optional fields default to required=False
OntologyFieldMapping(ontology_field="firstname", node_field="first_name")
```

If a `DuoUser` has no email and email is required, no `User` ontology node is created for that record.

### `eligible_for_source=False`

Default is `True`. Set to `False` when:

- The node type lacks sufficient data to create meaningful ontology nodes (e.g. no email for `User`).
- The node serves only as a connection point to existing ontology nodes.
- Required fields are not available or reliable enough.

```python
# AWS IAM users have no email — they can be linked, not used to create User nodes.
OntologyNodeMapping(
    node_label="AWSUser",
    eligible_for_source=False,
    fields=[
        OntologyFieldMapping(ontology_field="username", node_field="name"),
    ],
),
```

## Documenting ontology integration in schema docs

In `docs/root/modules/your_service/schema.md`, add the standard blockquote phrase right under the node description. See the `enrich-ontology` SKILL.md for the table of standard phrases by semantic label.

Example:

```markdown
### AWSAccount

Representation of an AWS Account.

> **Ontology Mapping**: This node has the extra label `Tenant` to enable cross-platform queries for organizational tenants across different systems (e.g., OktaOrganization, AzureTenant, GCPOrganization).

| Field | Description |
|-------|-------------|
| firstseen   | Timestamp of when a sync job discovered this node |
| name        | The name of the account                           |
| lastupdated | Timestamp of the last time the node was updated   |
| **id**      | The AWS Account ID number                         |
```
