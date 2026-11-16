from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class SweetTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description=(
            "Operator-supplied identifier for the Sweet tenant. The Sweet API has "
            "no endpoint that returns the tenant's own ID."
        ),
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sweet tenant was last synced.",
    )
    api_url: PropertyRef = PropertyRef(
        "api_url",
        description="Sweet API origin used for this tenant.",
    )


@dataclass(frozen=True)
class SweetTenantSchema(CartographyNodeSchema):
    """A Sweet Security tenant, the cleanup scope for every imported Sweet node."""

    label: str = "SweetTenant"
    properties: SweetTenantNodeProperties = SweetTenantNodeProperties()
    sub_resource_relationship: None = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
