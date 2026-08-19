from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class RunPodAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Configured stable RunPod account identifier."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RunPodAccountSchema(CartographyNodeSchema):
    """
    A RunPod account or team used as the tenant and security boundary for RunPod
    resources.
    """

    label: str = "RunPodAccount"
    properties: RunPodAccountNodeProperties = RunPodAccountNodeProperties()
