from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class JumpCloudTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="JumpCloud organization ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class JumpCloudTenantSchema(CartographyNodeSchema):
    """A JumpCloud organization containing managed resources."""

    label: str = "JumpCloudTenant"
    properties: JumpCloudTenantNodeProperties = JumpCloudTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Tenant"])
