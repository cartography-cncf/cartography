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
    id: PropertyRef = PropertyRef("id", description="Entra administrative unit ID.")
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Display name of the administrative unit."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description of the administrative unit."
    )
    visibility: PropertyRef = PropertyRef(
        "visibility", description="Visibility setting of the administrative unit."
    )
    membership_type: PropertyRef = PropertyRef(
        "membership_type", description="Membership type of the administrative unit."
    )
    is_member_management_restricted: PropertyRef = PropertyRef(
        "is_member_management_restricted",
        description="Whether member management is restricted.",
    )
    deleted_date_time: PropertyRef = PropertyRef(
        "deleted_date_time",
        description="Timestamp when the administrative unit was deleted.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the latest Cartography update.",
    )


@dataclass(frozen=True)
class EntraTenantToOURelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:EntraOU)<-[:RESOURCE]-(:AzureTenant)
class EntraOUToTenantRel(CartographyRelSchema):
    """Links a Microsoft tenant to one of its administrative units."""

    target_node_label: str = "AzureTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: EntraTenantToOURelProperties = EntraTenantToOURelProperties()


@dataclass(frozen=True)
class EntraOUSchema(CartographyNodeSchema):
    """An administrative unit in Microsoft Entra ID."""

    label: str = "EntraOU"
    properties: EntraOUNodeProperties = EntraOUNodeProperties()
    sub_resource_relationship: EntraOUToTenantRel = EntraOUToTenantRel()
