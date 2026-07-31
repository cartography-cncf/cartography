from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.workos.extra_labels import ENVIRONMENT


@dataclass(frozen=True)
class WorkOSEnvironmentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="WorkOS client ID identifying the environment."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSEnvironmentSchema(CartographyNodeSchema):
    """A WorkOS environment with the canonical Environment label."""

    label: str = "WorkOSEnvironment"
    properties: WorkOSEnvironmentNodeProperties = WorkOSEnvironmentNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([ENVIRONMENT])
