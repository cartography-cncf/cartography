"""
GitLab User Schema

GitLab users belong to organizations and can be members of groups.
Users are scoped to their organization for cleanup purposes.
"""

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
class GitLabUserNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab User node.

    Users can be members of groups and commit to projects.
    """

    id: PropertyRef = PropertyRef("web_url")  # Unique identifier (user profile URL)
    username: PropertyRef = PropertyRef("username", extra_index=True)  # GitLab username
    name: PropertyRef = PropertyRef("name")  # Full name
    state: PropertyRef = PropertyRef("state")  # User state (active, blocked, etc.)
    email: PropertyRef = PropertyRef("email")  # Email address (if public)
    is_admin: PropertyRef = PropertyRef("is_admin")  # Whether user is an admin
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabUserToOrganizationRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between GitLabUser and GitLabOrganization.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabUserToOrganizationRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabUser to GitLabOrganization.
    All users belong to an organization, used for cleanup scoping.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabUserToOrganizationRelProperties = (
        GitLabUserToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitLabUserToGroupRelProperties(CartographyRelProperties):
    """
    Properties for the MEMBER_OF relationship between GitLabUser and GitLabGroup.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    role: PropertyRef = PropertyRef(
        "role"
    )  # owner, maintainer, developer, reporter, guest
    access_level: PropertyRef = PropertyRef("access_level")  # 50, 40, 30, 20, 10


@dataclass(frozen=True)
class GitLabUserMemberOfGroupRel(CartographyRelSchema):
    """
    Relationship from GitLabUser to GitLabGroup via MEMBER_OF.
    Represents user membership in a group with access permissions.
    """

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("group_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF"
    properties: GitLabUserToGroupRelProperties = GitLabUserToGroupRelProperties()


@dataclass(frozen=True)
class GitLabUserCommittedToProjectRelProperties(CartographyRelProperties):
    """
    Properties for the COMMITTED_TO relationship between GitLabUser and GitLabProject.
    Tracks commit activity metadata.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    commit_count: PropertyRef = PropertyRef("commit_count")  # Number of commits
    last_commit_date: PropertyRef = PropertyRef(
        "last_commit_date"
    )  # Timestamp of most recent commit
    first_commit_date: PropertyRef = PropertyRef(
        "first_commit_date"
    )  # Timestamp of oldest commit


@dataclass(frozen=True)
class GitLabUserCommittedToProjectRel(CartographyRelSchema):
    """
    Relationship from GitLabUser to GitLabProject via COMMITTED_TO.
    Represents commit activity by a user on a project.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("project_url")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "COMMITTED_TO"
    properties: GitLabUserCommittedToProjectRelProperties = (
        GitLabUserCommittedToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabUserSchema(CartographyNodeSchema):
    """
    Schema for GitLab User nodes.

    Users belong to an organization (for cleanup scoping) and can be members of groups.
    Users can also have commit activity tracked to projects.
    The UserAccount label is used for ontology mapping across different platforms.
    """

    label: str = "GitLabUser"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["UserAccount"]
    )  # UserAccount label for ontology mapping
    properties: GitLabUserNodeProperties = GitLabUserNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabUserMemberOfGroupRel(),
            GitLabUserCommittedToProjectRel(),
        ],
    )
    sub_resource_relationship: GitLabUserToOrganizationRel = (
        GitLabUserToOrganizationRel()
    )
