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
class EntraOUNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    display_name: PropertyRef = PropertyRef("display_name")
    description: PropertyRef = PropertyRef("description")
    visibility: PropertyRef = PropertyRef("visibility")
    membership_type: PropertyRef = PropertyRef("membership_type")
    is_member_management_restricted: PropertyRef = PropertyRef(
        "is_member_management_restricted"
    )
    deleted_date_time: PropertyRef = PropertyRef("deleted_date_time")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class EntraTenantToOURelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraOU)<-[:RESOURCE]-(:AzureTenant)
class EntraOUToTenantRel(CartographyRelSchema):
    target_node_label: str = "EntraTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraTenantToOURelProperties = EntraTenantToOURelProperties()


@dataclass(frozen=True)
class EntraOUSchema(CartographyNodeSchema):
    label: str = "EntraOU"
    properties: EntraOUNodeProperties = EntraOUNodeProperties()
    sub_resource_relationship: EntraOUToTenantRel = EntraOUToTenantRel()
