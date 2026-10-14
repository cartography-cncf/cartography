from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADDomainToObjectRel
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class ADContainerSchema(CartographyNodeSchema):
    """An Active Directory container, such as `CN=Users`, keyed by GUID."""

    label: str = "ADContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AD_OBJECT])
    properties: ADObjectNodeProperties = ADObjectNodeProperties()
    sub_resource_relationship: ADDomainToObjectRel = ADDomainToObjectRel()
