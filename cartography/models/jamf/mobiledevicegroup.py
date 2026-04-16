from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class JamfMobileDeviceGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")
    membership_count: PropertyRef = PropertyRef("membership_count")
    is_smart: PropertyRef = PropertyRef("is_smart")


@dataclass(frozen=True)
class JamfTenantToMobileDeviceGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfTenantToMobileDeviceGroupRel(CartographyRelSchema):
    target_node_label: str = "JamfTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JamfTenantToMobileDeviceGroupRelProperties = (
        JamfTenantToMobileDeviceGroupRelProperties()
    )


@dataclass(frozen=True)
class JamfMobileDeviceGroupSchema(CartographyNodeSchema):
    label: str = "JamfMobileDeviceGroup"
    properties: JamfMobileDeviceGroupNodeProperties = (
        JamfMobileDeviceGroupNodeProperties()
    )
    sub_resource_relationship: JamfTenantToMobileDeviceGroupRel = (
        JamfTenantToMobileDeviceGroupRel()
    )
