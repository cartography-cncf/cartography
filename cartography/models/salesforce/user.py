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
class SalesforceUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("Id", description="Salesforce user ID.")
    username: PropertyRef = PropertyRef(
        "Username", extra_index=True, description="User login name."
    )
    name: PropertyRef = PropertyRef("Name", description="User display name.")
    first_name: PropertyRef = PropertyRef("FirstName", description="User first name.")
    last_name: PropertyRef = PropertyRef("LastName", description="User last name.")
    email: PropertyRef = PropertyRef(
        "Email", extra_index=True, description="User email address."
    )
    alias: PropertyRef = PropertyRef("Alias", description="Salesforce user alias.")
    is_active: PropertyRef = PropertyRef(
        "IsActive", description="Whether the user is active."
    )
    user_type: PropertyRef = PropertyRef(
        "UserType", description="Salesforce user type."
    )
    profile_id: PropertyRef = PropertyRef(
        "ProfileId", description="ID of the user's profile."
    )
    user_role_id: PropertyRef = PropertyRef(
        "UserRoleId", description="ID of the user's role."
    )
    manager_id: PropertyRef = PropertyRef(
        "ManagerId", description="ID of the user's manager."
    )
    department: PropertyRef = PropertyRef("Department", description="User department.")
    title: PropertyRef = PropertyRef("Title", description="User job title.")
    federation_identifier: PropertyRef = PropertyRef(
        "FederationIdentifier", description="User SSO federation identifier."
    )
    created_date: PropertyRef = PropertyRef(
        "CreatedDate", description="User creation timestamp."
    )
    last_login_date: PropertyRef = PropertyRef(
        "LastLoginDate", description="User last login timestamp."
    )
    last_password_change_date: PropertyRef = PropertyRef(
        "LastPasswordChangeDate", description="User last password change timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last update.",
    )


@dataclass(frozen=True)
class SalesforceUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUser)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceUserToOrganizationRel(CartographyRelSchema):
    """A Salesforce organization contains a user."""

    target_node_label: str = "SalesforceOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SalesforceUserToOrganizationRelProperties = (
        SalesforceUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserToProfileRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:UserAccount)-[:HAS_ROLE]->(:PermissionRole)
# (:SalesforceUser)-[:HAS_ROLE]->(:SalesforceProfile)
class SalesforceUserToProfileRel(CartographyRelSchema):
    """A Salesforce user has a baseline profile role."""

    target_node_label: str = "SalesforceProfile"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ProfileId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_ROLE"
    properties: SalesforceUserToProfileRelProperties = (
        SalesforceUserToProfileRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserToUserRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUser)-[:MEMBER_OF]->(:SalesforceUserRole)
class SalesforceUserToUserRoleRel(CartographyRelSchema):
    """A Salesforce user is a member of a user role."""

    target_node_label: str = "SalesforceUserRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("UserRoleId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: SalesforceUserToUserRoleRelProperties = (
        SalesforceUserToUserRoleRelProperties()
    )


@dataclass(frozen=True)
class SalesforceUserSchema(CartographyNodeSchema):
    """A Salesforce user account with the UserAccount label."""

    label: str = "SalesforceUser"
    # UserAccount label is used for ontology mapping
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: SalesforceUserNodeProperties = SalesforceUserNodeProperties()
    sub_resource_relationship: SalesforceUserToOrganizationRel = (
        SalesforceUserToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SalesforceUserToProfileRel(),
            SalesforceUserToUserRoleRel(),
        ]
    )
