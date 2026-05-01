# Advanced node properties

## Contents

- Conditional node labels
- Common schema mistakes (custom fields are ignored)
- Sub-resource relationships: deeper rationale

## Conditional node labels

> **Warning:** specialised feature, primarily for ontology mapping where a single source produces records that map to different semantic types. Most modules don't need this.

Apply a label only when the record matches certain conditions:

```python
from cartography.models.core.nodes import ConditionalNodeLabel, ExtraNodeLabels


@dataclass(frozen=True)
class ECRImageSchema(CartographyNodeSchema):
    label: str = "ECRImage"
    properties: ECRImageNodeProperties = ECRImageNodeProperties()
    sub_resource_relationship: ECRImageToAccountRel = ECRImageToAccountRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([
        ConditionalNodeLabel(label="Image",              conditions={"type": "IMAGE"}),
        ConditionalNodeLabel(label="ImageAttestation",   conditions={"type": "IMAGE_ATTESTATION"}),
        ConditionalNodeLabel(label="ImageManifestList",  conditions={"type": "IMAGE_MANIFEST_LIST"}),
    ])
```

### Primary use case: container registry images

ECR (and other container registries) store different artifact kinds with the same base schema but different semantic meaning:

| `type` value         | Ontology label       | Description                  |
| -------------------- | -------------------- | ---------------------------- |
| `IMAGE`              | `Image`              | Standard container image     |
| `IMAGE_ATTESTATION`  | `ImageAttestation`   | SLSA / Sigstore attestation  |
| `IMAGE_MANIFEST_LIST`| `ImageManifestList`  | Multi-arch manifest list     |

Without conditional labels, an `ECRImage` of type `IMAGE_ATTESTATION` would still get the generic `Image` ontology label.

### How it works

- String labels (e.g. `"SecurityFinding"`) are applied unconditionally during ingestion.
- `ConditionalNodeLabel` labels are applied in a separate query after ingestion, only on nodes matching all specified conditions.
- Conditions use **exact string equality** and combine with **AND** logic.
- Indexes are created automatically for conditional labels and their condition fields.
- When conditions change, labels are added or removed on subsequent syncs.

### Important notes

- Condition values must be strings (`"true"`, not `True`).
- All conditions must match (AND).

## Common schema mistakes (custom fields are ignored)

`CartographyNodeSchema` and `CartographyRelSchema` only recognise their standard fields. Anything you add is silently dropped.

```python
# DON'T
@dataclass(frozen=True)
class MyRelationship(CartographyRelSchema):
    target_node_label: str = "SomeNode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({"id": PropertyRef("some_id")})
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONNECTS_TO"
    properties: MyRelProperties = MyRelProperties()
    # These do nothing:
    conditional_match_property: str = "some_id"
    custom_flag: bool = True
    extra_config: dict = {"key": "value"}


@dataclass(frozen=True)
class MyNodeSchema(CartographyNodeSchema):
    label: str = "MyNode"
    properties: MyNodeProperties = MyNodeProperties()
    sub_resource_relationship: MyRel = MyRel()
    custom_setting: str = "ignored"  # does nothing
```

If you need conditional behaviour, handle it in `transform()` (set fields to `None` when relationships shouldn't be created, or filter records before `load()`).

### Standard `CartographyRelSchema` fields

- `target_node_label: str`
- `target_node_matcher: TargetNodeMatcher`
- `direction: LinkDirection`
- `rel_label: str`
- `properties: CartographyRelProperties` subclass
- `source_node_label: str` (MatchLink only)
- `source_node_matcher: SourceNodeMatcher` (MatchLink only)
- `source_node_sub_resource: MatchLinkSubResource` (MatchLink only, optional)

### Standard `CartographyNodeSchema` fields

- `label: str`
- `properties: CartographyNodeProperties` subclass
- `sub_resource_relationship: CartographyRelSchema` subclass
- `other_relationships: OtherRelationships` (optional)
- `extra_node_labels: ExtraNodeLabels` (optional)
- `scoped_cleanup: bool` (optional, defaults to `True` — should almost never be overridden, only for modules without a clear tenant-like entity)

## Sub-resource relationships: deeper rationale

The `sub_resource_relationship` always refers to a tenant-like node representing the ownership boundary of the resource.

**Correct examples:**
- AWS resources -> `AWSAccount`
- Azure resources -> `AzureSubscription`
- GCP resources -> `GCPProject`
- SaaS apps -> `<Service>Tenant`
- GitHub resources -> `GitHubOrganization`

**Incorrect:**
- Pointing to a parent resource that is not tenant-like (e.g. `ECSTaskDefinition -> ECSTask`).
- Pointing to infrastructure components (e.g. `ECSContainer -> ECSTask`).
- Pointing to logical groupings that are not organisational boundaries.

### Why it matters

1. **Cleanup operations.** Cartography uses the sub-resource relationship to scope `GraphJob.from_node_schema()` cleanups; misrouting it deletes the wrong rows.
2. **Data organisation.** Tenant-like nodes provide natural data boundaries.
3. **Access control.** Tenant edges enable proper isolation.
4. **Consistency.** Same modelling pattern across modules is what makes cross-module queries possible.

### ECS container definition example

```python
# CORRECT — sub-resource is the AWS account, business edge is the task definition.
@dataclass(frozen=True)
class ECSContainerDefinitionSchema(CartographyNodeSchema):
    label: str = "ECSContainerDefinition"
    properties: ECSContainerDefinitionNodeProperties = ECSContainerDefinitionNodeProperties()
    sub_resource_relationship: ECSContainerDefinitionToAWSAccountRel = ECSContainerDefinitionToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships([
        ECSContainerDefinitionToTaskDefinitionRel(),
    ])


@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("AWS_ID", set_in_kwargs=True),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerDefinitionToAWSAccountRelProperties = ECSContainerDefinitionToAWSAccountRelProperties()


@dataclass(frozen=True)
class ECSContainerDefinitionToTaskDefinitionRel(CartographyRelSchema):
    target_node_label: str = "ECSTaskDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher({
        "id": PropertyRef("_taskDefinitionArn"),
    })
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONTAINER_DEFINITION"
    properties: ECSContainerDefinitionToTaskDefinitionRelProperties = ECSContainerDefinitionToTaskDefinitionRelProperties()
```
