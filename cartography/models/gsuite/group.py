from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GSuiteGroupNodeProperties(CartographyNodeProperties):
    """
    GSuite group node properties
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Group identifiers and basic info
    group_id: PropertyRef = PropertyRef("id")  # Alias for id
    email: PropertyRef = PropertyRef("email", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    description: PropertyRef = PropertyRef("description")

    # Group settings
    admin_created: PropertyRef = PropertyRef("adminCreated")
    direct_members_count: PropertyRef = PropertyRef("directMembersCount")

    # Metadata
    etag: PropertyRef = PropertyRef("etag")
    kind: PropertyRef = PropertyRef("kind")

    # Tenant relationship
    customer_id: PropertyRef = PropertyRef("CUSTOMER_ID", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToTenantRelProperties(CartographyRelProperties):
    """
    Properties for GSuite group to tenant relationship
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GSuiteGroupToTenantRel(CartographyRelSchema):
    """
    Relationship from GSuite group to GSuite tenant
    """

    target_node_label: str = "GSuiteTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CUSTOMER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GSuiteGroupToTenantRelProperties = GSuiteGroupToTenantRelProperties()


@dataclass(frozen=True)
class GSuiteGroupSchema(CartographyNodeSchema):
    """
    GSuite group node schema
    """

    label: str = "GSuiteGroup"
    properties: GSuiteGroupNodeProperties = GSuiteGroupNodeProperties()
    sub_resource_relationship: GSuiteGroupToTenantRel = GSuiteGroupToTenantRel()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["GCPPrincipal"]
    )  # Keep existing label
