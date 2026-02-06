"""
GitHub Container Image Schema

Represents container images stored in GitHub Container Registry (GHCR).
Images are identified by their digest (sha256:...) and can be referenced by multiple tags.
Manifest lists (multi-architecture images) contain references to platform-specific images.
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
class GitHubContainerImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    uri: PropertyRef = PropertyRef("uri", extra_index=True)
    media_type: PropertyRef = PropertyRef("media_type")
    schema_version: PropertyRef = PropertyRef("schema_version")
    type: PropertyRef = PropertyRef("type", extra_index=True)
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    variant: PropertyRef = PropertyRef("variant")
    child_image_digests: PropertyRef = PropertyRef("child_image_digests")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitHubContainerImage to GitHubOrganization.
    Images are scoped to organizations for cleanup and to allow cross-package deduplication.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerImageToOrgRelProperties = (
        GitHubContainerImageToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageContainsImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageContainsImageRel(CartographyRelSchema):
    """
    Relationship from a manifest list to its platform-specific child images.
    Only applies to images with type="manifest_list".
    """

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("child_image_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GitHubContainerImageContainsImageRelProperties = (
        GitHubContainerImageContainsImageRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageSchema(CartographyNodeSchema):
    """
    Schema for GitHub Container Image nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitHubOrganization for cleanup
    - CONTAINS_IMAGE: From manifest lists to platform-specific images
    """

    label: str = "GitHubContainerImage"
    properties: GitHubContainerImageNodeProperties = (
        GitHubContainerImageNodeProperties()
    )
    sub_resource_relationship: GitHubContainerImageToOrgRel = (
        GitHubContainerImageToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitHubContainerImageContainsImageRel(),
        ],
    )
