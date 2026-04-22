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


@dataclass(frozen=True)
class OktaUserTypeNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    created: PropertyRef = PropertyRef("created")
    created_by: PropertyRef = PropertyRef("created_by")
    default: PropertyRef = PropertyRef("default")
    description: PropertyRef = PropertyRef("description")
    display_name: PropertyRef = PropertyRef("display_name")
    last_updated: PropertyRef = PropertyRef("last_updated")
    last_updated_by: PropertyRef = PropertyRef("last_updated_by")
    name: PropertyRef = PropertyRef("name")


@dataclass(frozen=True)
class OktaUserTypeToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaUserToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUserType)<-[:RESOURCE]-(:OktaOrganization)
class OktaUserTypeToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaUserToOktaOrganizationRelProperties = (
        OktaUserToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
# (:OktaUserType)<-[:HAS_TYPE]-(:OktaUser)
class OktaUserTypeToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"type": PropertyRef("id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TYPE"
    properties: OktaUserTypeToOktaUserRelProperties = (
        OktaUserTypeToOktaUserRelProperties()
    )


@dataclass(frozen=True)
class OktaUserTypeSchema(CartographyNodeSchema):
    label: str = "OktaUserType"
    properties: OktaUserTypeNodeProperties = OktaUserTypeNodeProperties()
    sub_resource_relationship: OktaUserTypeToOktaOrganizationRel = (
        OktaUserTypeToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[OktaUserTypeToOktaUserRel()],
    )


####
# User Role
####


@dataclass(frozen=True)
class OktaUserRoleNodeProperties(CartographyNodeProperties):
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
class OktaUserRoleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUserRole)<-[:RESOURCE]-(:OktaOrganization)
class OktaUserRoleToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaUserRoleToOktaOrganizationRelProperties = (
        OktaUserRoleToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
class OktaUserRoleSchema(CartographyNodeSchema):
    label: str = "OktaUserRole"
    properties: OktaUserRoleNodeProperties = OktaUserRoleNodeProperties()
    sub_resource_relationship: OktaUserRoleToOktaOrganizationRel = (
        OktaUserRoleToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[],
    )


@dataclass(frozen=True)
class OktaUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    # Top-level Okta User fields
    created: PropertyRef = PropertyRef("created")
    status: PropertyRef = PropertyRef("status")
    activated: PropertyRef = PropertyRef("activated")
    status_changed: PropertyRef = PropertyRef("status_changed")
    last_login: PropertyRef = PropertyRef("last_login")
    okta_last_updated: PropertyRef = PropertyRef("okta_last_updated")
    password_changed: PropertyRef = PropertyRef("password_changed")
    transition_to_status: PropertyRef = PropertyRef("transition_to_status")
    type: PropertyRef = PropertyRef("type")
    # UserProfile — standard Okta schema fields
    login: PropertyRef = PropertyRef("login")
    email: PropertyRef = PropertyRef("email", extra_index=True)
    second_email: PropertyRef = PropertyRef("second_email")
    first_name: PropertyRef = PropertyRef("first_name")
    last_name: PropertyRef = PropertyRef("last_name")
    middle_name: PropertyRef = PropertyRef("middle_name")
    honorific_prefix: PropertyRef = PropertyRef("honorific_prefix")
    honorific_suffix: PropertyRef = PropertyRef("honorific_suffix")
    display_name: PropertyRef = PropertyRef("display_name")
    nick_name: PropertyRef = PropertyRef("nick_name")
    profile_url: PropertyRef = PropertyRef("profile_url")
    locale: PropertyRef = PropertyRef("locale")
    preferred_language: PropertyRef = PropertyRef("preferred_language")
    timezone: PropertyRef = PropertyRef("timezone")
    user_type: PropertyRef = PropertyRef("user_type")
    title: PropertyRef = PropertyRef("title")
    department: PropertyRef = PropertyRef("department")
    division: PropertyRef = PropertyRef("division")
    organization: PropertyRef = PropertyRef("organization")
    cost_center: PropertyRef = PropertyRef("cost_center")
    employee_number: PropertyRef = PropertyRef("employee_number")
    manager: PropertyRef = PropertyRef("manager")
    manager_id: PropertyRef = PropertyRef("manager_id")
    mobile_phone: PropertyRef = PropertyRef("mobile_phone")
    primary_phone: PropertyRef = PropertyRef("primary_phone")
    street_address: PropertyRef = PropertyRef("street_address")
    city: PropertyRef = PropertyRef("city")
    state: PropertyRef = PropertyRef("state")
    zip_code: PropertyRef = PropertyRef("zip_code")
    country_code: PropertyRef = PropertyRef("country_code")
    postal_address: PropertyRef = PropertyRef("postal_address")
    # JSON-encoded tenant-specific custom profile attributes
    custom_attributes: PropertyRef = PropertyRef("custom_attributes")


@dataclass(frozen=True)
class OktaUserToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:OktaUser)<-[:RESOURCE]-(:OktaOrganization)
class OktaUserToOktaOrganizationRel(CartographyRelSchema):
    target_node_label: str = "OktaOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("OKTA_ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: OktaUserToOrgRelProperties = OktaUserToOrgRelProperties()


@dataclass(frozen=True)
class OktaUserToOktaUserRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class OktaUserToOktaUserRoleRel(CartographyRelSchema):
    # (:OktaUser)-[:HAS_ROLE]->(:OktaUserRole)
    target_node_label: str = "OktaUserRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("role_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: OktaUserToOktaUserRoleRelProperties = (
        OktaUserToOktaUserRoleRelProperties()
    )


@dataclass(frozen=True)
class OktaUserSchema(CartographyNodeSchema):
    label: str = "OktaUser"
    properties: OktaUserNodeProperties = OktaUserNodeProperties()
    sub_resource_relationship: OktaUserToOktaOrganizationRel = (
        OktaUserToOktaOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            OktaUserToOktaUserRoleRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
