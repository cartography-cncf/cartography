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

    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric GitLab user ID.",
    )
    username: PropertyRef = PropertyRef(
        "username",
        extra_index=True,
        description="GitLab username.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Full name of the user.",
    )
    state: PropertyRef = PropertyRef(
        "state",
        description="GitLab account state, such as active or blocked.",
    )
    email: PropertyRef = PropertyRef(
        "email",
        description="Email address exposed for the user.",
    )
    is_admin: PropertyRef = PropertyRef(
        "is_admin",
        description="Whether the user is a GitLab administrator.",
    )
    web_url: PropertyRef = PropertyRef(
        "web_url",
        extra_index=True,
        description="URL for viewing the user in GitLab.",
    )
    gitlab_url: PropertyRef = PropertyRef(
        "gitlab_url",
        extra_index=True,
        description="URL of the GitLab instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


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
        {
            "id": PropertyRef("org_id", set_in_kwargs=True),
            "gitlab_url": PropertyRef("gitlab_url", set_in_kwargs=True),
        },
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
        "role",
        description="GitLab membership role, such as owner, maintainer, or developer.",
    )
    access_level: PropertyRef = PropertyRef(
        "access_level",
        description="Numeric GitLab access level for the group membership.",
    )


@dataclass(frozen=True)
class GitLabUserMemberOfGroupRel(CartographyRelSchema):
    """
    Relationship from GitLabUser to GitLabGroup via MEMBER_OF.
    Represents user membership in a group with access permissions.
    """

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("group_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
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
    commit_count: PropertyRef = PropertyRef(
        "commit_count",
        description="Number of commits made by the user to the project.",
    )
    last_commit_date: PropertyRef = PropertyRef(
        "last_commit_date",
        description="Timestamp of the user's most recent commit to the project.",
    )
    first_commit_date: PropertyRef = PropertyRef(
        "first_commit_date",
        description="Timestamp of the user's oldest commit to the project.",
    )


@dataclass(frozen=True)
class GitLabUserCommittedToProjectRel(CartographyRelSchema):
    """
    Relationship from GitLabUser to GitLabProject via COMMITTED_TO.
    Represents commit activity by a user on a project.
    """

    target_node_label: str = "GitLabProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("project_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "COMMITTED_TO"
    properties: GitLabUserCommittedToProjectRelProperties = (
        GitLabUserCommittedToProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabUserSchema(CartographyNodeSchema):
    """A current GitLab organization or group member."""

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
