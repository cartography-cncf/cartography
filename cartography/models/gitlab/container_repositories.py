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

    id: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    path: PropertyRef = PropertyRef("path", extra_index=True)
    repository_id: PropertyRef = PropertyRef("id")
    project_id: PropertyRef = PropertyRef("project_id")
    created_at: PropertyRef = PropertyRef("created_at")
    cleanup_policy_started_at: PropertyRef = PropertyRef("cleanup_policy_started_at")
    tags_count: PropertyRef = PropertyRef("tags_count")
    size: PropertyRef = PropertyRef("size")
    status: PropertyRef = PropertyRef("status")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabContainerRepositoryToOrgRelProperties = (
        GitLabContainerRepositoryToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerRepositorySchema(CartographyNodeSchema):
    """
    Schema for GitLab Container Repository nodes.
    """

    label: str = "GitLabContainerRepository"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: GitLabContainerRepositoryNodeProperties = (
        GitLabContainerRepositoryNodeProperties()
    )
    sub_resource_relationship: GitLabContainerRepositoryToOrgRel = (
        GitLabContainerRepositoryToOrgRel()
    )
