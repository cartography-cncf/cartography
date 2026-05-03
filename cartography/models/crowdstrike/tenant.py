from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema


@dataclass(frozen=True)
class CrowdstrikeTenantNodeProperties(CartographyNodeProperties):
    """
    Represents a CrowdStrike customer tenant identified by its CID. Hosts and
    Spotlight vulnerabilities reported by the API carry a `cid` field that
    points to this tenant; CrowdstrikeTenant is the cleanup scope for those
    nodes.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CrowdstrikeTenantSchema(CartographyNodeSchema):
    label: str = "CrowdstrikeTenant"
    properties: CrowdstrikeTenantNodeProperties = CrowdstrikeTenantNodeProperties()
