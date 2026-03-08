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
class AIBOMWorkflowNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    workflow_id: PropertyRef = PropertyRef("workflow_id")
    function: PropertyRef = PropertyRef("function")
    file_path: PropertyRef = PropertyRef("file_path")
    line: PropertyRef = PropertyRef("line")
    distance: PropertyRef = PropertyRef("distance")


@dataclass(frozen=True)
class AIBOMWorkflowToComponentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AIBOMWorkflowToComponentRel(CartographyRelSchema):
    """Reverse side of AIBOMComponent -[:IN_WORKFLOW]-> AIBOMWorkflow.

    Declared here so that GraphJob can generate cleanup queries for
    AIBOMWorkflow nodes (without an other_relationships entry, the
    cleanup builder returns an empty job for unscoped schemas with
    no relationships).
    """

    target_node_label: str = "AIBOMComponent"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "IN_WORKFLOW"
    properties: AIBOMWorkflowToComponentRelProperties = (
        AIBOMWorkflowToComponentRelProperties()
    )


@dataclass(frozen=True)
class AIBOMWorkflowSchema(CartographyNodeSchema):
    label: str = "AIBOMWorkflow"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: AIBOMWorkflowNodeProperties = AIBOMWorkflowNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [AIBOMWorkflowToComponentRel()],
    )
