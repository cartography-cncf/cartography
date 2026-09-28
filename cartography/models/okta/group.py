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
from cartography.models.ontology.labels import PERMISSION_ROLE
from cartography.models.ontology.labels import USER_GROUP

####
# User Role
####


@dataclass(frozen=True)
class OktaGroupRoleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    description: PropertyRef = PropertyRef(
        "description", description="Okta description."
    )
    label: PropertyRef = PropertyRef("label", description="Okta label.")
    assignment_type: PropertyRef = PropertyRef(
        "assignment_type", description="Okta assignment type."
    )
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Okta last updated."
    )
    status: PropertyRef = PropertyRef("status", description="Okta status.")
    role_type: PropertyRef = PropertyRef("role_type", description="Okta role type.")
    name: PropertyRef = PropertyRef("name", description="Okta name.")


@dataclass(frozen=True)
class OktaGroupRoleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaGroupRole)<-[:RESOURCE]-(:OktaOrganization)
class OktaGroupRoleToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])


@dataclass(frozen=True)
class OktaGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    # Legacy fields for backward compatibility
    name: PropertyRef = PropertyRef("name", extra_index=True, description="Okta name.")
    description: PropertyRef = PropertyRef(
        "description", description="Okta description."
    )
    sam_account_name: PropertyRef = PropertyRef(
        "sam_account_name", description="Okta sam account name."
    )
    dn: PropertyRef = PropertyRef("dn", description="Okta dn.")
    windows_domain_qualified_name: PropertyRef = PropertyRef(
        "windows_domain_qualified_name",
        description="Okta windows domain qualified name.",
    )
    external_id: PropertyRef = PropertyRef(
        "external_id", description="Okta external ID."
    )
    # New fields from SDK v3.x
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    last_membership_updated: PropertyRef = PropertyRef(
        "last_membership_updated", description="Okta last membership updated."
    )
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Okta last updated."
    )
    object_class: PropertyRef = PropertyRef(
        "object_class", description="Okta object class."
    )
    group_type: PropertyRef = PropertyRef("group_type", description="Okta group type.")


@dataclass(frozen=True)
class OktaGroupToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaGroup)<-[:RESOURCE]-(:OktaOrganization)
class OktaGroupToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaGroupToOktaOrganizationRelProperties = (
        OktaGroupToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaGroupToOktaUserRel(CartographyRelSchema):
    # (:OktaGroup)<-[:MEMBER_OF]-(:OktaUser)
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "user_id", description="Identifier of the related Okta user."
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF"
    properties: OktaGroupToOktaUserRelProperties = OktaGroupToOktaUserRelProperties()


# DEPRECATED: replaced by MEMBER_OF, will be removed in v1.0.0.
@dataclass(frozen=True)
class OktaGroupToOktaUserDeprecatedRel(CartographyRelSchema):
    # (:OktaGroup)<-[:MEMBER_OF_OKTA_GROUP]-(:OktaUser)
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "user_id", description="Identifier of the related Okta user."
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "MEMBER_OF_OKTA_GROUP"
    properties: OktaGroupToOktaUserRelProperties = OktaGroupToOktaUserRelProperties()


@dataclass(frozen=True)
class OktaGroupToOktaGroupRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaGroupToOktaGroupRoleRel(CartographyRelSchema):
    # (:OktaGroup)-[:HAS_ROLE]->(:OktaGroupRole)
    target_node_label: str = "OktaGroupRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "role_id", description="Identifier of the related Okta role."
            )
        },
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
        rels=[
            OktaGroupToOktaUserRel(),
            OktaGroupToOktaUserDeprecatedRel(),
            OktaGroupToOktaGroupRoleRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_GROUP])


@dataclass(frozen=True)
class OktaGroupRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    name: PropertyRef = PropertyRef("name", description="Okta name.")
    status: PropertyRef = PropertyRef("status", description="Okta status.")
    last_updated: PropertyRef = PropertyRef(
        "last_updated", description="Okta last updated."
    )
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    # Condition properties - supports expression, group_membership, and complex types
    condition_type: PropertyRef = PropertyRef(
        "condition_type", description="Okta condition type."
    )
    conditions: PropertyRef = PropertyRef("conditions", description="Okta conditions.")
    expression_type: PropertyRef = PropertyRef(
        "expression_type", description="Okta expression type."
    )
    # People filter properties
    exclusions: PropertyRef = PropertyRef("exclusions", description="Okta exclusions.")
    inclusions: PropertyRef = PropertyRef("inclusions", description="Okta inclusions.")
    assigned_groups: PropertyRef = PropertyRef(
        "assigned_groups", description="Okta assigned groups."
    )


@dataclass(frozen=True)
class OktaGroupRuleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaGroupRule)<-[:RESOURCE]-(:OktaOrganization)
class OktaGroupRuleToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "OKTA_ORG_ID",
                set_in_kwargs=True,
                description="Identifier of the owning Okta organization.",
            )
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaGroupRuleToOktaOrganizationRelProperties = (
        OktaGroupRuleToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaGroupToOktaGroupRuleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaGroupToOktaGroupRuleRel(CartographyRelSchema):
    # (:OktaGroupRule)-[:ASSIGNED_BY_GROUP_RULE]->(:OktaGroup)
    target_node_label: str = "OktaGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "group_id", description="Identifier of the related Okta group."
            )
        },
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
