"""
GitHub Container Package Tag Schema

Represents tags within a GitHub container package.
Tags are pointers to specific container images identified by digest.
Multiple tags can point to the same image digest (e.g., "latest" and "v1.0.0").
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
class GitHubContainerPackageTagNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    package_id: PropertyRef = PropertyRef("package_id")
    version_id: PropertyRef = PropertyRef("version_id")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    html_url: PropertyRef = PropertyRef("html_url")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerPackageTagToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerPackageTagToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitHubContainerPackageTag to GitHubOrganization.
    All container registry resources are scoped to the organization for cleanup.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerPackageTagToOrgRelProperties = (
        GitHubContainerPackageTagToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerPackageTagToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerPackageTagToImageRel(CartographyRelSchema):
    """
    Links a tag to the container image it references via digest.
    Multiple tags can reference the same image.
    """

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REFERENCES"
    properties: GitHubContainerPackageTagToImageRelProperties = (
        GitHubContainerPackageTagToImageRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerPackageTagToPackageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerPackageTagToPackageRel(CartographyRelSchema):
    """
    Links a tag to its parent container package.
    """

    target_node_label: str = "GitHubContainerPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("package_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TAG"
    properties: GitHubContainerPackageTagToPackageRelProperties = (
        GitHubContainerPackageTagToPackageRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerPackageTagSchema(CartographyNodeSchema):
    """
    Schema for GitHub Container Package Tag nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitHubOrganization for cleanup
    - HAS_TAG: Links from GitHubContainerPackage to this tag
    - REFERENCES: Links to GitHubContainerImage via digest
    """

    label: str = "GitHubContainerPackageTag"
    properties: GitHubContainerPackageTagNodeProperties = (
        GitHubContainerPackageTagNodeProperties()
    )
    sub_resource_relationship: GitHubContainerPackageTagToOrgRel = (
        GitHubContainerPackageTagToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubContainerPackageTagToPackageRel(),
            GitHubContainerPackageTagToImageRel(),
        ],
    )
