from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class SemgrepDeploymentProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique integer identifier for the deployment.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Name of the security organization connected to the deployment.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="Lowercase deployment identifier used to query the Semgrep API.",
    )


@dataclass(frozen=True)
class SemgrepDeploymentSchema(CartographyNodeSchema):
    """A Semgrep Cloud deployment containing an organization's security resources."""

    label: str = "SemgrepDeployment"
    properties: SemgrepDeploymentProperties = SemgrepDeploymentProperties()
