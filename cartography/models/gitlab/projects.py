"""
GitLab Project Schema

In GitLab, projects are repositories/codebases that belong to groups.
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
class GitLabProjectNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Project node.

    Projects are GitLab's equivalent of repositories.
    """

    id: PropertyRef = PropertyRef(
        "id",
        description="Numeric GitLab project ID.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Project name.",
    )
    path: PropertyRef = PropertyRef(
        "path",
        extra_index=True,
        description="URL path slug of the project.",
    )
    path_with_namespace: PropertyRef = PropertyRef(
        "path_with_namespace",
        extra_index=True,
        description="Full project path including its namespace.",
    )
    web_url: PropertyRef = PropertyRef(
        "web_url",
        extra_index=True,
        description="URL for viewing the project in GitLab.",
    )
    gitlab_url: PropertyRef = PropertyRef(
        "gitlab_url",
        extra_index=True,
        description="URL of the GitLab instance.",
    )
    description: PropertyRef = PropertyRef(
        "description",
        description="Human-readable description of the project.",
    )
    visibility: PropertyRef = PropertyRef(
        "visibility",
        description="Project visibility: private, internal, or public.",
    )
    default_branch: PropertyRef = PropertyRef(
        "default_branch",
        description="Name of the project's default branch.",
    )
    archived: PropertyRef = PropertyRef(
        "archived",
        description="Whether the project is archived.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when GitLab created the project.",
    )
    last_activity_at: PropertyRef = PropertyRef(
        "last_activity_at",
        description="Timestamp of the project's most recent activity.",
    )
    languages: PropertyRef = PropertyRef(
        "languages",
        extra_index=True,
        description="JSON object mapping detected programming languages to percentages.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GitLabGroupCanAccessProjectRelProperties(CartographyRelProperties):
    """
    Properties for the CAN_ACCESS relationship between GitLabGroup and GitLabProject.

    This represents group sharing in GitLab, where a group is given access to a project.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    access_level: PropertyRef = PropertyRef(
        "access_level",
        description="Numeric GitLab access level granted to the group.",
    )


@dataclass(frozen=True)
class GitLabGroupCanAccessProjectRel(CartographyRelSchema):
    """
    Relationship from GitLabGroup to GitLabProject representing group access.
    """

    target_node_label: str = "GitLabGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("group_id"),
            "gitlab_url": PropertyRef("gitlab_url"),
        },
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_ACCESS"
    properties: GitLabGroupCanAccessProjectRelProperties = (
        GitLabGroupCanAccessProjectRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectToGroupRelProperties(CartographyRelProperties):
    """
    Properties for the MEMBER_OF relationship between GitLabProject and GitLabGroup.
    Represents the immediate parent group of a project (for projects in nested groups).
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectToGroupRel(CartographyRelSchema):
    """
    Relationship from GitLabProject to GitLabGroup via MEMBER_OF.
    Represents the immediate parent group of a project (for projects in nested groups).
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
    properties: GitLabProjectToGroupRelProperties = GitLabProjectToGroupRelProperties()


@dataclass(frozen=True)
class GitLabProjectToOrganizationRelProperties(CartographyRelProperties):
    """
    Properties for the RESOURCE relationship between GitLabProject and GitLabOrganization.
    Used for cleanup scoping - all projects belong to an organization.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabProjectToOrganizationRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabProject to GitLabOrganization.
    All projects belong to an organization, used for cleanup scoping.
    Projects are cleaned up per organization.
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
    properties: GitLabProjectToOrganizationRelProperties = (
        GitLabProjectToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class GitLabProjectSchema(CartographyNodeSchema):
    """A GitLab project containing a source code repository."""

    label: str = "GitLabProject"
    properties: GitLabProjectNodeProperties = GitLabProjectNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabGroupCanAccessProjectRel(),  # Group has access to project (sharing)
            GitLabProjectToGroupRel(),  # Project belongs to group (for projects in nested groups)
        ],
    )
    sub_resource_relationship: GitLabProjectToOrganizationRel = (
        GitLabProjectToOrganizationRel()
    )
    # Add GitLabRepository for compatibility and CodeRepository for ontology queries.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["GitLabRepository", "CodeRepository"]
    )
