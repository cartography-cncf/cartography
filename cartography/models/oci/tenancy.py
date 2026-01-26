from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class OCITenancyNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ocid")
    ocid: PropertyRef = PropertyRef("ocid", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class OCITenancySchema(CartographyNodeSchema):
    label: str = "OCITenancy"
    properties: OCITenancyNodeProperties = OCITenancyNodeProperties()
    # OCITenancy is the root tenant-like object, so it has no sub_resource_relationship
    scoped_cleanup: bool = False
