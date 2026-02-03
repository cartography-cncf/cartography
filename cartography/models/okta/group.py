from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
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
    # DEPRECATED: OktaAdministrationRole was the old shared label, kept for backward compatibility
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["OktaAdministrationRole"])


@dataclass(frozen=True)
class OktaGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Legacy fields for backward compatibility
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    sam_account_name: PropertyRef = PropertyRef("sam_account_name")
    dn: PropertyRef = PropertyRef("dn")
    windows_domain_qualified_name: PropertyRef = PropertyRef(
        "windows_domain_qualified_name"
    )
    external_id: PropertyRef = PropertyRef("external_id")
    # New fields from SDK v3.x
    created: PropertyRef = PropertyRef("created")
    last_membership_updated: PropertyRef = PropertyRef("last_membership_updated")
    last_updated: PropertyRef = PropertyRef("last_updated")
    object_class: PropertyRef = PropertyRef("object_class")
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
    # (:OktaGroup)<-[:MEMBER_OF_OKTA_GROUP]-(:OktaUser)
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("user_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
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
class OktaGroupToOktaAdminRoleRel(CartographyRelSchema):
    # DEPRECATED: Old relationship label, kept for backward compatibility
    # (:OktaGroup)-[:MEMBER_OF_OKTA_ROLE]->(:OktaAdministrationRole)
    target_node_label: str = "OktaAdministrationRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_OKTA_ROLE"
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
        rels=[
            OktaGroupToOktaUserRel(),
            OktaGroupToOktaGroupRoleRel(),
            OktaGroupToOktaAdminRoleRel(),  # DEPRECATED: backward compatibility
        ],
    )


@dataclass(frozen=True)
class OktaGroupRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    status: PropertyRef = PropertyRef("status")
    last_updated: PropertyRef = PropertyRef("last_updated")
    created: PropertyRef = PropertyRef("created")
    # Condition properties - supports expression, group_membership, and complex types
    condition_type: PropertyRef = PropertyRef("condition_type")
    conditions: PropertyRef = PropertyRef("conditions")
    expression_type: PropertyRef = PropertyRef("expression_type")
    # People filter properties
    exclusions: PropertyRef = PropertyRef("exclusions")
    inclusions: PropertyRef = PropertyRef("inclusions")
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
    # (:OktaGroupRule)-[:ASSIGNED_BY_GROUP_RULE]->(:OktaGroup)
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
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
