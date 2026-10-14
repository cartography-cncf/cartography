from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADDomainToObjectRel
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels


@dataclass(frozen=True)
class ADOUNodeProperties(ADObjectNodeProperties):
    blocksinheritance: PropertyRef = PropertyRef(
        "blocksinheritance",
        description="Whether the OU blocks GPO inheritance from its parents.",
    )


@dataclass(frozen=True)
class ADOUSchema(CartographyNodeSchema):
    """An Active Directory organizational unit, keyed by GUID."""

    label: str = "ADOU"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([AD_OBJECT])
    properties: ADOUNodeProperties = ADOUNodeProperties()
    sub_resource_relationship: ADDomainToObjectRel = ADDomainToObjectRel()
