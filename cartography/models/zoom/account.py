from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class ZoomAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Zoom account ID used for server-to-server OAuth."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ZoomAccountSchema(CartographyNodeSchema):
    """A Zoom account containing users and pending invitations.

    Ontology Mapping: The Tenant label enables cross-provider tenant queries.
    """

    label: str = "ZoomAccount"
    properties: ZoomAccountNodeProperties = ZoomAccountNodeProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
