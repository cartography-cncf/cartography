from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class AIBOMComponentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    category: PropertyRef = PropertyRef("category", extra_index=True)
    instance_id: PropertyRef = PropertyRef("instance_id")
    assigned_target: PropertyRef = PropertyRef("assigned_target")
    file_path: PropertyRef = PropertyRef("file_path")
    line_number: PropertyRef = PropertyRef("line_number")
    model_name: PropertyRef = PropertyRef("model_name")
    framework: PropertyRef = PropertyRef("framework")
    label: PropertyRef = PropertyRef("label")
    metadata_json: PropertyRef = PropertyRef("metadata_json")
    manifest_digest: PropertyRef = PropertyRef("manifest_digest", extra_index=True)


@dataclass(frozen=True)
class AIBOMComponentDetectedInRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMComponentDetectedInRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("manifest_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DETECTED_IN"
    properties: AIBOMComponentDetectedInRelProperties = (
        AIBOMComponentDetectedInRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentInWorkflowRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMComponentInWorkflowRel(CartographyRelSchema):
    target_node_label: str = "AIBOMWorkflow"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("workflow_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN_WORKFLOW"
    properties: AIBOMComponentInWorkflowRelProperties = (
        AIBOMComponentInWorkflowRelProperties()
    )


@dataclass(frozen=True)
class AIBOMComponentSchema(CartographyNodeSchema):
    label: str = "AIBOMComponent"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: AIBOMComponentNodeProperties = AIBOMComponentNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AIBOMComponentDetectedInRel(),
            AIBOMComponentInWorkflowRel(),
        ],
    )
