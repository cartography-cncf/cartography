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
from cartography.models.ontology.labels import USER_ACCOUNT


@dataclass(frozen=True)
class OktaUserTypeNodeProperties(CartographyNodeProperties):
    # Upstream SDK bug: `okta.models.user_type.UserType` declares only `id`
    # (the skinny shape used for the embedded reference on User), so pydantic
    # drops every other field the `/api/v1/meta/types/user` endpoint returns
    # (name, display_name, description, created, created_by, last_updated,
    # last_updated_by, default). `list_user_types` is typed as
    # `List[UserType]`, so the richer metadata never reaches us.
    # Tracked upstream at https://github.com/okta/okta-sdk-python/issues/535.
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaUserTypeToOktaUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaUserToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaUserType)<-[:RESOURCE]-(:OktaOrganization)
class OktaUserTypeToOktaOrganizationRel(CartographyRelSchema):
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
    properties: OktaUserToOktaOrganizationRelProperties = (
        OktaUserToOktaOrganizationRelProperties()
    )


@dataclass(frozen=True)
# (:OktaUserType)<-[:HAS_TYPE]-(:OktaUser)
class OktaUserTypeToOktaUserRel(CartographyRelSchema):
    target_node_label: str = "OktaUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "type": PropertyRef(
                "id", description="Unique identifier for the Okta resource."
            )
        },
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
class OktaUserRoleToOktaOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaUserRole)<-[:RESOURCE]-(:OktaOrganization)
class OktaUserRoleToOktaOrganizationRel(CartographyRelSchema):
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([PERMISSION_ROLE])


@dataclass(frozen=True)
class OktaUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Unique identifier for the Okta resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )
    # Top-level Okta User fields
    created: PropertyRef = PropertyRef("created", description="Okta created.")
    status: PropertyRef = PropertyRef("status", description="Okta status.")
    activated: PropertyRef = PropertyRef("activated", description="Okta activated.")
    status_changed: PropertyRef = PropertyRef(
        "status_changed", description="Okta status changed."
    )
    last_login: PropertyRef = PropertyRef("last_login", description="Okta last login.")
    okta_last_updated: PropertyRef = PropertyRef(
        "okta_last_updated", description="Okta okta last updated."
    )
    password_changed: PropertyRef = PropertyRef(
        "password_changed", description="Okta password changed."
    )
    transition_to_status: PropertyRef = PropertyRef(
        "transition_to_status", description="Okta transition to status."
    )
    type: PropertyRef = PropertyRef("type", description="Okta type.")
    # UserProfile — standard Okta schema fields
    login: PropertyRef = PropertyRef("login", description="Okta login.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="Okta email."
    )
    second_email: PropertyRef = PropertyRef(
        "second_email", description="Okta second email."
    )
    first_name: PropertyRef = PropertyRef("first_name", description="Okta first name.")
    last_name: PropertyRef = PropertyRef("last_name", description="Okta last name.")
    middle_name: PropertyRef = PropertyRef(
        "middle_name", description="Okta middle name."
    )
    honorific_prefix: PropertyRef = PropertyRef(
        "honorific_prefix", description="Okta honorific prefix."
    )
    honorific_suffix: PropertyRef = PropertyRef(
        "honorific_suffix", description="Okta honorific suffix."
    )
    display_name: PropertyRef = PropertyRef(
        "display_name", description="Okta display name."
    )
    nick_name: PropertyRef = PropertyRef("nick_name", description="Okta nick name.")
    profile_url: PropertyRef = PropertyRef(
        "profile_url", description="Okta profile URL."
    )
    locale: PropertyRef = PropertyRef("locale", description="Okta locale.")
    preferred_language: PropertyRef = PropertyRef(
        "preferred_language", description="Okta preferred language."
    )
    timezone: PropertyRef = PropertyRef("timezone", description="Okta timezone.")
    user_type: PropertyRef = PropertyRef("user_type", description="Okta user type.")
    title: PropertyRef = PropertyRef("title", description="Okta title.")
    department: PropertyRef = PropertyRef("department", description="Okta department.")
    division: PropertyRef = PropertyRef("division", description="Okta division.")
    organization: PropertyRef = PropertyRef(
        "organization", description="Okta organization."
    )
    cost_center: PropertyRef = PropertyRef(
        "cost_center", description="Okta cost center."
    )
    employee_number: PropertyRef = PropertyRef(
        "employee_number", description="Okta employee number."
    )
    manager: PropertyRef = PropertyRef("manager", description="Okta manager.")
    manager_id: PropertyRef = PropertyRef("manager_id", description="Okta manager ID.")
    mobile_phone: PropertyRef = PropertyRef(
        "mobile_phone", description="Okta mobile phone."
    )
    primary_phone: PropertyRef = PropertyRef(
        "primary_phone", description="Okta primary phone."
    )
    street_address: PropertyRef = PropertyRef(
        "street_address", description="Okta street address."
    )
    city: PropertyRef = PropertyRef("city", description="Okta city.")
    state: PropertyRef = PropertyRef("state", description="Okta state.")
    zip_code: PropertyRef = PropertyRef("zip_code", description="Okta zip code.")
    country_code: PropertyRef = PropertyRef(
        "country_code", description="Okta country code."
    )
    postal_address: PropertyRef = PropertyRef(
        "postal_address", description="Okta postal address."
    )
    # JSON-encoded tenant-specific custom profile attributes
    custom_attributes: PropertyRef = PropertyRef(
        "custom_attributes", description="Okta custom attributes."
    )


@dataclass(frozen=True)
class OktaUserToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
# (:OktaUser)<-[:RESOURCE]-(:OktaOrganization)
class OktaUserToOktaOrganizationRel(CartographyRelSchema):
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
    properties: OktaUserToOrgRelProperties = OktaUserToOrgRelProperties()


@dataclass(frozen=True)
class OktaUserToOktaUserRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this resource.",
    )


@dataclass(frozen=True)
class OktaUserToOktaUserRoleRel(CartographyRelSchema):
    # (:OktaUser)-[:HAS_ROLE]->(:OktaUserRole)
    target_node_label: str = "OktaUserRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef(
                "role_id", description="Identifier of the related Okta role."
            )
        },
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([USER_ACCOUNT])
