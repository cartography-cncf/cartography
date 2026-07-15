from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class LastpassTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="LastPass tenant ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class LastpassTenantSchema(CartographyNodeSchema):
    """Representation of a LastPass tenant."""

    label: str = "LastpassTenant"
    properties: LastpassTenantNodeProperties = LastpassTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
