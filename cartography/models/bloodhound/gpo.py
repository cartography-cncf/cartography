from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADDomainToObjectRel
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class ADGPONodeProperties(ADObjectNodeProperties):
    gpcpath: PropertyRef = PropertyRef(
        "gpcpath",
        description="SYSVOL path of the group policy template.",
    )


@dataclass(frozen=True)
class ADGPOSchema(CartographyNodeSchema):
    """An Active Directory group policy object, keyed by GUID."""

    label: str = "ADGPO"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AD_OBJECT])
    properties: ADGPONodeProperties = ADGPONodeProperties()
    sub_resource_relationship: ADDomainToObjectRel = ADDomainToObjectRel()
