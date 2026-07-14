from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SocketDevOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Unique Socket.dev organization identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Organization display name.",
    )
    slug: PropertyRef = PropertyRef(
        "slug",
        extra_index=True,
        description="Organization slug used in Socket.dev API URLs.",
    )
    plan: PropertyRef = PropertyRef(
        "plan",
        description="Organization subscription plan.",
    )
    image: PropertyRef = PropertyRef(
        "image",
        description="Organization image URL.",
    )


@dataclass(frozen=True)
class SocketDevOrganizationSchema(CartographyNodeSchema):
    """A Socket.dev organization containing monitored resources."""

    label: str = "SocketDevOrganization"
    properties: SocketDevOrganizationNodeProperties = (
        SocketDevOrganizationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
