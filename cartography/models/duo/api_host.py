from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class DuoApiHostNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Duo API hostname.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DuoApiHostSchema(CartographyNodeSchema):
    """A Duo API host that contains resources for a Duo tenant."""

    label: str = "DuoApiHost"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
    properties: DuoApiHostNodeProperties = DuoApiHostNodeProperties()
