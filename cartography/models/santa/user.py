from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class SantaUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    email: PropertyRef = PropertyRef("email", extra_index=True)
    principal_name: PropertyRef = PropertyRef("principal_name", extra_index=True)
    display_name: PropertyRef = PropertyRef("display_name")
    source_name: PropertyRef = PropertyRef("source_name")


@dataclass(frozen=True)
class SantaUserSchema(CartographyNodeSchema):
    label: str = "SantaUser"
    scoped_cleanup: bool = False
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label is used for ontology mapping.
    properties: SantaUserNodeProperties = SantaUserNodeProperties()
