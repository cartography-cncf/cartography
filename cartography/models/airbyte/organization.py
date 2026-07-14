from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class AirbyteOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("organizationId", description="Organization UUID.")
    name: PropertyRef = PropertyRef(
        "organizationName", description="Organization name."
    )
    email: PropertyRef = PropertyRef(
        "email", description="Organization contact email address."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class AirbyteOrganizationSchema(CartographyNodeSchema):
    """An Airbyte organization with the Tenant label."""

    label: str = "AirbyteOrganization"
    properties: AirbyteOrganizationNodeProperties = AirbyteOrganizationNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
