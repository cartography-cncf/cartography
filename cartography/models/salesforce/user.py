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
    id: PropertyRef = PropertyRef("Id")
    username: PropertyRef = PropertyRef("Username", extra_index=True)
    name: PropertyRef = PropertyRef("Name")
    first_name: PropertyRef = PropertyRef("FirstName")
    last_name: PropertyRef = PropertyRef("LastName")
    email: PropertyRef = PropertyRef("Email", extra_index=True)
    alias: PropertyRef = PropertyRef("Alias")
    is_active: PropertyRef = PropertyRef("IsActive")
    user_type: PropertyRef = PropertyRef("UserType")
    profile_id: PropertyRef = PropertyRef("ProfileId")
    user_role_id: PropertyRef = PropertyRef("UserRoleId")
    manager_id: PropertyRef = PropertyRef("ManagerId")
    department: PropertyRef = PropertyRef("Department")
    title: PropertyRef = PropertyRef("Title")
    federation_identifier: PropertyRef = PropertyRef("FederationIdentifier")
    created_date: PropertyRef = PropertyRef("CreatedDate")
    last_login_date: PropertyRef = PropertyRef("LastLoginDate")
    last_password_change_date: PropertyRef = PropertyRef("LastPasswordChangeDate")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SalesforceUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SalesforceUser)<-[:RESOURCE]-(:SalesforceOrganization)
class SalesforceUserToOrganizationRel(CartographyRelSchema):
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
