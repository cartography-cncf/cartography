from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class WorkOSOrganizationMembershipNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    user_id: PropertyRef = PropertyRef("user_id", extra_index=True)
    organization_id: PropertyRef = PropertyRef("organization_id", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    role_id: PropertyRef = PropertyRef("role_id")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkOSOrganizationMembershipToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSOrganizationMembership)
class WorkOSOrganizationMembershipToEnvironmentRel(CartographyRelSchema):
    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSOrganizationMembershipToEnvironmentRelProperties = (
        WorkOSOrganizationMembershipToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationMembershipToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSOrganizationMembership)<-[:MEMBER_OF]-(:WorkOSUser)
class WorkOSOrganizationMembershipToUserRel(CartographyRelSchema):
    target_node_label: str = "WorkOSUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: WorkOSOrganizationMembershipToUserRelProperties = (
        WorkOSOrganizationMembershipToUserRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationMembershipToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSOrganizationMembership)-[:IN]->(:WorkOSOrganization)
class WorkOSOrganizationMembershipToOrganizationRel(CartographyRelSchema):
    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IN"
    properties: WorkOSOrganizationMembershipToOrganizationRelProperties = (
        WorkOSOrganizationMembershipToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationMembershipToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSOrganizationMembership)-[:WITH_ROLE]->(:WorkOSRole)
class WorkOSOrganizationMembershipToRoleRel(CartographyRelSchema):
    target_node_label: str = "WorkOSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"slug": PropertyRef("roles", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WITH_ROLE"
    properties: WorkOSOrganizationMembershipToRoleRelProperties = (
        WorkOSOrganizationMembershipToRoleRelProperties()
    )


@dataclass(frozen=True)
class WorkOSOrganizationMembershipSchema(CartographyNodeSchema):
    label: str = "WorkOSOrganizationMembership"
    properties: WorkOSOrganizationMembershipNodeProperties = (
        WorkOSOrganizationMembershipNodeProperties()
    )
    sub_resource_relationship: WorkOSOrganizationMembershipToEnvironmentRel = (
        WorkOSOrganizationMembershipToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            WorkOSOrganizationMembershipToUserRel(),
            WorkOSOrganizationMembershipToOrganizationRel(),
            WorkOSOrganizationMembershipToRoleRel(),
        ],
    )
