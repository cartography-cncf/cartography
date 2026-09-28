from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class TenableTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Configured Tenable tenant ID or normalized base URL."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TenableTenantSchema(CartographyNodeSchema):
    """A Tenable tenant that scopes imported resources."""

    label: str = "TenableTenant"
    properties: TenableTenantNodeProperties = TenableTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
