from dataclasses import dataclass

from cartography.models.bloodhound.common import AD_OBJECT
from cartography.models.bloodhound.common import ADDomainToObjectRel
from cartography.models.bloodhound.common import ADObjectNodeProperties
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.ontology.labels import USER_GROUP


@dataclass(frozen=True)
class ADGroupNodeProperties(ADObjectNodeProperties):
    samaccountname: PropertyRef = PropertyRef(
        "samaccountname",
        extra_index=True,
        description="Pre-Windows 2000 group name.",
    )
    admincount: PropertyRef = PropertyRef(
        "admincount",
        description="Whether AdminSDHolder protects the group, which usually means it is or was privileged.",
    )


@dataclass(frozen=True)
class ADGroupSchema(CartographyNodeSchema):
    """An Active Directory group, keyed by SID.

    Built-in groups such as Domain Users carry a domain-prefixed identifier, for
    example `EXAMPLE.LOCAL-S-1-5-32-544`.
    """

    label: str = "ADGroup"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP, AD_OBJECT])
    properties: ADGroupNodeProperties = ADGroupNodeProperties()
    sub_resource_relationship: ADDomainToObjectRel = ADDomainToObjectRel()
