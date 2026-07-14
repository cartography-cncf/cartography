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
class WorkOSDirectoryUserNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="WorkOS directory user ID.")
    idp_id: PropertyRef = PropertyRef(
        "idp_id",
        extra_index=True,
        description="User ID assigned by the identity provider.",
    )
    directory_id: PropertyRef = PropertyRef(
        "directory_id",
        extra_index=True,
        description="ID of the user's WorkOS directory.",
    )
    organization_id: PropertyRef = PropertyRef(
        "organization_id",
        extra_index=True,
        description="ID of the user's WorkOS organization.",
    )
    first_name: PropertyRef = PropertyRef("first_name", description="User first name.")
    last_name: PropertyRef = PropertyRef("last_name", description="User last name.")
    email: PropertyRef = PropertyRef(
        "email", extra_index=True, description="User email address."
    )
    state: PropertyRef = PropertyRef("state", description="Directory user state.")
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="RFC 3339 timestamp when the directory user was created.",
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at",
        description="RFC 3339 timestamp when the directory user was updated.",
    )
    custom_attributes: PropertyRef = PropertyRef(
        "custom_attributes",
        description="Custom user attributes from the identity provider.",
    )
    raw_attributes: PropertyRef = PropertyRef(
        "raw_attributes", description="Raw user attributes from the identity provider."
    )
    roles: PropertyRef = PropertyRef(
        "roles", description="Directory role slugs assigned by the identity provider."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update."
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToEnvironmentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSEnvironment)-[:RESOURCE]->(:WorkOSDirectoryUser)
class WorkOSDirectoryUserToEnvironmentRel(CartographyRelSchema):
    """The WorkOS environment contains this directory user as a resource."""

    target_node_label: str = "WorkOSEnvironment"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("WORKOS_CLIENT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkOSDirectoryUserToEnvironmentRelProperties = (
        WorkOSDirectoryUserToEnvironmentRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToDirectoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectory)-[:HAS]->(:WorkOSDirectoryUser)
class WorkOSDirectoryUserToDirectoryRel(CartographyRelSchema):
    """The WorkOS directory contains this directory user."""

    target_node_label: str = "WorkOSDirectory"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("directory_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: WorkOSDirectoryUserToDirectoryRelProperties = (
        WorkOSDirectoryUserToDirectoryRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectoryUser)-[:BELONGS_TO]->(:WorkOSOrganization)
class WorkOSDirectoryUserToOrganizationRel(CartographyRelSchema):
    """The WorkOS directory user belongs to its organization."""

    target_node_label: str = "WorkOSOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("organization_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BELONGS_TO"
    properties: WorkOSDirectoryUserToOrganizationRelProperties = (
        WorkOSDirectoryUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserToGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:WorkOSDirectoryUser)-[:MEMBER_OF]->(:WorkOSDirectoryGroup)
class WorkOSDirectoryUserToGroupRel(CartographyRelSchema):
    """The WorkOS directory user is a member of each assigned directory group."""

    target_node_label: str = "WorkOSDirectoryGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: WorkOSDirectoryUserToGroupRelProperties = (
        WorkOSDirectoryUserToGroupRelProperties()
    )


@dataclass(frozen=True)
class WorkOSDirectoryUserSchema(CartographyNodeSchema):
    """A directory-synchronized WorkOS user with the canonical UserAccount label."""

    label: str = "WorkOSDirectoryUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["UserAccount"])
    properties: WorkOSDirectoryUserNodeProperties = WorkOSDirectoryUserNodeProperties()
    sub_resource_relationship: WorkOSDirectoryUserToEnvironmentRel = (
        WorkOSDirectoryUserToEnvironmentRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        rels=[
            WorkOSDirectoryUserToDirectoryRel(),
            WorkOSDirectoryUserToOrganizationRel(),
            WorkOSDirectoryUserToGroupRel(),
        ],
    )
