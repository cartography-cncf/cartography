"""
GitLab Container Image Schema

Represents container images stored in GitLab container registries.
Images are identified by their digest (sha256:...) and can be referenced by multiple tags.
Manifest lists (multi-architecture images) contain references to platform-specific images.

See: https://docs.gitlab.com/ee/user/packages/container_registry/
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
class GitLabContainerImageNodeProperties(CartographyNodeProperties):
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
class GitLabContainerImageToOrgRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitLabContainerImage to GitLabOrganization.
    Images are scoped to organizations for cleanup and to allow cross-project deduplication.
    """

    target_node_label: str = "GitLabOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitLabContainerImageToOrgRelProperties = (
        GitLabContainerImageToOrgRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerImageContainsImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitLabContainerImageContainsImageRel(CartographyRelSchema):
    """
    Relationship from a manifest list to its platform-specific child images.
    Only applies to images with type="manifest_list".
    """

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("child_image_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GitLabContainerImageContainsImageRelProperties = (
        GitLabContainerImageContainsImageRelProperties()
    )


@dataclass(frozen=True)
class GitLabContainerImageSchema(CartographyNodeSchema):
    """
    Schema for GitLab Container Image nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitLabOrganization for cleanup
    - CONTAINS_IMAGE: From manifest lists to platform-specific images
    """

    label: str = "GitLabContainerImage"
    properties: GitLabContainerImageNodeProperties = (
        GitLabContainerImageNodeProperties()
    )
    sub_resource_relationship: GitLabContainerImageToOrgRel = (
        GitLabContainerImageToOrgRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GitLabContainerImageContainsImageRel(),
        ],
    )
