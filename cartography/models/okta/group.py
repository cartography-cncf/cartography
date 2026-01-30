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

####
# User Role
####


@dataclass(frozen=True)
class OktaGroupRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    created: PropertyRef = PropertyRef("created")
    description: PropertyRef = PropertyRef("description")
    label: PropertyRef = PropertyRef("label")
    assignment_type: PropertyRef = PropertyRef("assignment_type")
    last_updated: PropertyRef = PropertyRef("last_updated")
    status: PropertyRef = PropertyRef("status")
    role_type: PropertyRef = PropertyRef("role_type")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class OktaGroupRoleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaGroupRole)<-[:RESOURCE]-(:OktaOrganization)
class OktaGroupRoleToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaGroupRoleToOktaOrganizationRelProperties = (
        OktaGroupRoleToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupRoleSchema(CartographyNodeSchema):
    label: str = "OktaGroupRole"
    properties: OktaGroupRoleNodeProperties = OktaGroupRoleNodeProperties()
    sub_resource_relationship: OktaGroupRoleToOktaOrganizationRel = (
        OktaGroupRoleToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[],
    )


@dataclass(frozen=True)
class OktaGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    created: PropertyRef = PropertyRef("created")
    last_membership_updated: PropertyRef = PropertyRef("last_membership_updated")
    last_updated: PropertyRef = PropertyRef("last_updated")
    object_class: PropertyRef = PropertyRef("object_class")
    profile_description: PropertyRef = PropertyRef("profile_description")
    profile_name: PropertyRef = PropertyRef("profile_name", extra_index=True)
    group_type: PropertyRef = PropertyRef("group_type")


@dataclass(frozen=True)
class OktaGroupToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaGroup)<-[:RESOURCE]-(:OktaOrganization)
class OktaGroupToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaGroupToOktaOrganizationRelProperties = (
        OktaGroupToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaGroupToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_OKTA_GROUP"
    properties: OktaGroupToOktaUserRelProperties = OktaGroupToOktaUserRelProperties()


@dataclass(frozen=True)
class OktaGroupToOktaGroupRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaGroupToOktaGroupRoleRel(CartographyRelSchema):
    # (:OktaGroup)-[:HAS_ROLE]->(:OktaGroupRole)
    target_node_label: str = "OktaGroupRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: OktaGroupToOktaGroupRoleRelProperties = (
        OktaGroupToOktaGroupRoleRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupSchema(CartographyNodeSchema):
    label: str = "OktaGroup"
    properties: OktaGroupNodeProperties = OktaGroupNodeProperties()
    sub_resource_relationship: OktaGroupToOktaOrganizationRel = (
        OktaGroupToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OktaGroupToOktaUserRel(), OktaGroupToOktaGroupRoleRel()],
    )


@dataclass(frozen=True)
class OktaGroupRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    last_updated: PropertyRef = PropertyRef("last_updated")
    created: PropertyRef = PropertyRef("created")
    conditions: PropertyRef = PropertyRef("conditions")
    exclusions: PropertyRef = PropertyRef("exclusions")
    assigned_groups: PropertyRef = PropertyRef("assigned_groups")


@dataclass(frozen=True)
class OktaGroupRuleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaGroupRule)<-[:RESOURCE]-(:OktaOrganization)
class OktaGroupRuleToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaGroupRuleToOktaOrganizationRelProperties = (
        OktaGroupRuleToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupToOktaGroupRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaGroupToOktaGroupRuleRel(CartographyRelSchema):
    # (:OktaGroup)<-[:ASSIGNED_BY_GROUP_RULE]-(:OktaGroupRule)
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "ASSIGNED_BY_GROUP_RULE"
    properties: OktaGroupToOktaGroupRuleRelProperties = (
        OktaGroupToOktaGroupRuleRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupRuleSchema(CartographyNodeSchema):
    label: str = "OktaGroupRule"
    properties: OktaGroupRuleNodeProperties = OktaGroupRuleNodeProperties()
    sub_resource_relationship: OktaGroupRuleToOktaOrganizationRel = (
        OktaGroupRuleToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OktaGroupToOktaGroupRuleRel()],
    )
