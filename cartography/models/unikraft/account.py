from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class UnikraftAccountNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Unikraft Cloud account UUID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    status: PropertyRef = PropertyRef(
        "status", description="Quota status reported for this account."
    )
    message: PropertyRef = PropertyRef(
        "message", description="Additional status information from the quotas API."
    )


@dataclass(frozen=True)
class UnikraftAccountSchema(CartographyNodeSchema):
    """Represents a Unikraft Cloud account, identified by its quota UUID."""

    label: str = "UnikraftAccount"
    properties: UnikraftAccountNodeProperties = UnikraftAccountNodeProperties()
    sub_resource_relationship = None
    other_relationships = None
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
