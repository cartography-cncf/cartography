"""
GitLab Container Repository Schema

Represents container registry repositories in GitLab projects.
Each project can have multiple container repositories (e.g., project root, subpaths like /app, /worker).
Container repositories store container images as tags.

See: https://docs.gitlab.com/ee/api/container_registry.html
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
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabContainerRepositoryNodeProperties(CartographyNodeProperties):
    """
    Properties for a GitLab Container Repository node.

    Container repositories are collections of container images within a project's registry.
    A single project can have multiple container repositories at different paths.
    """

    id: PropertyRef = PropertyRef(
        "location",
        description="Full registry location of the container repository.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description="Container repository name.",
    )
    path: PropertyRef = PropertyRef(
        "path",
        extra_index=True,
        description="Container repository path within the GitLab project.",
    )
    repository_id: PropertyRef = PropertyRef(
        "id",
        description="Numeric GitLab container repository ID.",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id",
        description="Numeric ID of the parent GitLab project.",
    )
    created_at: PropertyRef = PropertyRef(
        "created_at",
        description="Timestamp when GitLab created the container repository.",
    )
    cleanup_policy_started_at: PropertyRef = PropertyRef(
        "cleanup_policy_started_at",
        description="Timestamp when the repository cleanup policy last started.",
    )
    tags_count: PropertyRef = PropertyRef(
        "tags_count",
        description="Number of tags in the container repository.",
    )
    size: PropertyRef = PropertyRef(
        "size",
        description="Container repository size in bytes.",
    )
    status: PropertyRef = PropertyRef(
        "status",
        description="GitLab container repository status.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class GitLabContainerRepositoryToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerRepositoryToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabContainerRepository to GitLabOrganization.
    All container registry resources are scoped to the organization for cleanup.
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
    properties: GitLabContainerRepositoryToOrgRelProperties = (
        GitLabContainerRepositoryToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerRepositorySchema(CartographyNodeSchema):
    """A container registry repository belonging to a GitLab project."""

    label: str = "GitLabContainerRepository"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: GitLabContainerRepositoryNodeProperties = (
        GitLabContainerRepositoryNodeProperties()
    )
    sub_resource_relationship: GitLabContainerRepositoryToOrgRel = (
        GitLabContainerRepositoryToOrgRel()
    )
