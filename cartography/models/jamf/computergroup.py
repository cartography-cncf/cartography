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
class JamfComputerGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Jamf computer group ID.")
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Friendly name of the group.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Group description.",
    )
    membership_count: PropertyRef = PropertyRef(
        "membership_count",
        description="Number of members reported by Jamf.",
    )
    is_smart: PropertyRef = PropertyRef(
        "is_smart",
        description="Whether this is a smart group.",
    )


@dataclass(frozen=True)
class JamfTenantToComputerGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class JamfTenantToComputerGroupRel(CartographyRelSchema):
    """Links a Jamf tenant to one of its computer groups."""

    target_node_label: str = "JamfTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: JamfTenantToComputerGroupRelProperties = (
        JamfTenantToComputerGroupRelProperties()
    )


@dataclass(frozen=True)
class JamfComputerGroupSchema(CartographyNodeSchema):
    """A group of computers managed by Jamf."""

    label: str = "JamfComputerGroup"
    properties: JamfComputerGroupNodeProperties = JamfComputerGroupNodeProperties()
    sub_resource_relationship: JamfTenantToComputerGroupRel = (
        JamfTenantToComputerGroupRel()
    )
