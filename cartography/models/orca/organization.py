from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class OrcaOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Stable Orca organization identifier.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp when this Orca organization was last seen.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Display name of the Orca organization.",
    )
    api_url: PropertyRef = PropertyRef(
        "api_url",
        description="Regional Orca API base URL used for this organization.",
    )


@dataclass(frozen=True)
class OrcaOrganizationSchema(CartographyNodeSchema):
    """An Orca organization whose security findings are ingested by Cartography."""

    label: str = "OrcaOrganization"
    properties: OrcaOrganizationNodeProperties = OrcaOrganizationNodeProperties()
    sub_resource_relationship: None = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    scoped_cleanup: bool = False
