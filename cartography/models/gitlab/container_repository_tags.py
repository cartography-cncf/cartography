"""
GitLab Container Repository Tag Schema

Represents tags within a GitLab container repository.
Tags are pointers to specific container images identified by digest.
Multiple tags can point to the same image digest (e.g., "latest" and "v1.0.0").

See: https://docs.gitlab.com/ee/api/container_registry.html
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GitLabContainerRepositoryTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("location")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    path: PropertyRef = PropertyRef("path")
    repository_location: PropertyRef = PropertyRef("repository_location")
    revision: PropertyRef = PropertyRef("revision")
    short_revision: PropertyRef = PropertyRef("short_revision")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    created_at: PropertyRef = PropertyRef("created_at")
    total_size: PropertyRef = PropertyRef("total_size")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerRepositoryTagToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerRepositoryTagToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabContainerRepositoryTag to GitLabOrganization.
    All container registry resources are scoped to the organization for cleanup.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabContainerRepositoryTagToOrgRelProperties = (
        GitLabContainerRepositoryTagToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerRepositoryTagToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerRepositoryTagToImageRel(CartographyRelSchema):
    """
    Links a tag to the container image it references via digest.
    Multiple tags can reference the same image.
    """

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES"
    properties: GitLabContainerRepositoryTagToImageRelProperties = (
        GitLabContainerRepositoryTagToImageRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerRepositoryTagToRepoRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerRepositoryTagToRepoRel(CartographyRelSchema):
    """
    Links a tag to its parent container repository.
    """

    target_node_label: str = "GitLabContainerRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_location")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TAG"
    properties: GitLabContainerRepositoryTagToRepoRelProperties = (
        GitLabContainerRepositoryTagToRepoRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerRepositoryTagSchema(CartographyNodeSchema):
    """
    Schema for GitLab Container Repository Tag nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitLabOrganization for cleanup
    - HAS_TAG: Links from GitLabContainerRepository to this tag
    - REFERENCES: Links to GitLabContainerImage via digest
    """

    label: str = "GitLabContainerRepositoryTag"
    properties: GitLabContainerRepositoryTagNodeProperties = (
        GitLabContainerRepositoryTagNodeProperties()
    )
    sub_resource_relationship: GitLabContainerRepositoryTagToOrgRel = (
        GitLabContainerRepositoryTagToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabContainerRepositoryTagToRepoRel(),
            GitLabContainerRepositoryTagToImageRel(),
        ],
    )
