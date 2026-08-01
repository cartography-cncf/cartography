from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class JamfTenantNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Jamf tenant ID represented by the configured base URI.",
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfTenantSchema(CartographyNodeSchema):
    """A Jamf tenant identified by its configured base URI."""

    label: str = "JamfTenant"
    properties: JamfTenantNodeProperties = JamfTenantNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
