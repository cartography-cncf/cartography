from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class AzureTenantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Microsoft tenant ID.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AzureTenantSchema(CartographyNodeSchema):
    """A Microsoft tenant, with EntraTenant retained as a compatibility label."""

    label: str = "AzureTenant"
    properties: AzureTenantProperties = AzureTenantProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])
