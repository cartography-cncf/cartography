from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class WizTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Wiz tenant identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Wiz tenant was last seen.",
    )
    graphql_url: PropertyRef = PropertyRef(
        "graphql_url",
        description="Wiz GraphQL API endpoint used for this tenant.",
    )


@dataclass(frozen=True)
class WizTenantSchema(CartographyNodeSchema):
    label: str = "WizTenant"
    properties: WizTenantNodeProperties = WizTenantNodeProperties()
    sub_resource_relationship: None = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
