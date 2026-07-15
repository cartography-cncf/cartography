from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.workos.extra_labels import EnvironmentLabel


@dataclass(frozen=True)
class WorkOSEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSEnvironmentSchema(CartographyNodeSchema):
    label: str = "WorkOSEnvironment"
    properties: WorkOSEnvironmentNodeProperties = WorkOSEnvironmentNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([EnvironmentLabel()])
