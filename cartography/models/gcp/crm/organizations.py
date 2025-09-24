from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class GCPOrganizationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    orgname: PropertyRef = PropertyRef("name")
    displayname: PropertyRef = PropertyRef("displayName")
    lifecyclestate: PropertyRef = PropertyRef("lifecycleState")


@dataclass(frozen=True)
class GCPOrganizationSchema(CartographyNodeSchema):
    label: str = "GCPOrganization"
    properties: GCPOrganizationNodeProperties = GCPOrganizationNodeProperties()
    # sub_resource_relationship is None by default - Organizations are top-level resources
