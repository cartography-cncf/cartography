from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class FlyOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Fly.io organization slug.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name", description="Organization display name.")
    slug: PropertyRef = PropertyRef(
        "slug", extra_index=True, description="Organization slug."
    )
    internal_numeric_id: PropertyRef = PropertyRef(
        "internal_numeric_id", description="Fly.io internal numeric organization ID."
    )


@dataclass(frozen=True)
class FlyOrganizationSchema(CartographyNodeSchema):
    """Represents a Fly.io organization."""

    label: str = "FlyOrganization"
    properties: FlyOrganizationNodeProperties = FlyOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
