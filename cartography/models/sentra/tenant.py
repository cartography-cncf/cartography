from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class SentraTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Sentra organization ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Sentra organization was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Display name of the Sentra organization.",
    )
    organization_type: PropertyRef = PropertyRef(
        "organization_type",
        description="Sentra organization type.",
    )
    api_url: PropertyRef = PropertyRef(
        "api_url",
        description="Sentra API base URL used for this organization.",
    )


@dataclass(frozen=True)
class SentraTenantSchema(CartographyNodeSchema):
    """A Sentra organization whose data security posture Cartography ingests."""

    label: str = "SentraTenant"
    properties: SentraTenantNodeProperties = SentraTenantNodeProperties()
    sub_resource_relationship: None = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    scoped_cleanup: bool = False
