from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


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
class AIBOMWorkflowSchema(CartographyNodeSchema):
    label: str = "AIBOMWorkflow"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([])
    properties: AIBOMWorkflowNodeProperties = AIBOMWorkflowNodeProperties()
