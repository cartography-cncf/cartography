from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class ScalewayOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="ID of the Scaleway Organization")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayOrganizationSchema(CartographyNodeSchema):
    """Represents an Organization in Scaleway."""

    label: str = "ScalewayOrganization"
    properties: ScalewayOrganizationNodeProperties = (
        ScalewayOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
