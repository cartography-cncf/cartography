"""
GitHub Container Image Schema.

Represents container images stored in GitHub Container Registry (ghcr.io).
Images are identified by their digest (sha256:...) and can be referenced by
multiple tags. Manifest lists (multi-architecture images) contain references
to platform-specific images.

See: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
"""

from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
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
    source_uri: PropertyRef = PropertyRef("source_uri", extra_index=True)
    source_revision: PropertyRef = PropertyRef("source_revision")
    source_file: PropertyRef = PropertyRef("source_file")
    parent_image_uri: PropertyRef = PropertyRef("parent_image_uri")
    parent_image_digest: PropertyRef = PropertyRef("parent_image_digest")
    child_image_digests: PropertyRef = PropertyRef("child_image_digests")
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")
    head_layer_diff_id: PropertyRef = PropertyRef("head_layer_diff_id")
    tail_layer_diff_id: PropertyRef = PropertyRef("tail_layer_diff_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageToOrgRel(CartographyRelSchema):
    """
    Sub-resource relationship from GitHubContainerImage to GitHubOrganization.
    Images are scoped to organizations for cleanup and to allow cross-package
    deduplication.
    """

    target_node_label: str = "GitHubOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("org_url", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GitHubContainerImageRelProperties = GitHubContainerImageRelProperties()


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
    properties: GitHubContainerImageRelProperties = GitHubContainerImageRelProperties()


@dataclass(frozen=True)
class GitHubContainerImageToLayerRel(CartographyRelSchema):
    """
    Relationship from an image to its constituent layers.
    Only applies to single-image manifests (type="image").
    """

    target_node_label: str = "GitHubContainerImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("layer_diff_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAYER"
    properties: GitHubContainerImageRelProperties = GitHubContainerImageRelProperties()


@dataclass(frozen=True)
class GitHubContainerImageToHeadLayerRel(CartographyRelSchema):
    target_node_label: str = "GitHubContainerImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("head_layer_diff_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HEAD"
    properties: GitHubContainerImageRelProperties = GitHubContainerImageRelProperties()


@dataclass(frozen=True)
class GitHubContainerImageToTailLayerRel(CartographyRelSchema):
    target_node_label: str = "GitHubContainerImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("tail_layer_diff_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "TAIL"
    properties: GitHubContainerImageRelProperties = GitHubContainerImageRelProperties()


@dataclass(frozen=True)
class GitHubContainerImageToParentImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    from_attestation: PropertyRef = PropertyRef("from_attestation")
    parent_image_uri: PropertyRef = PropertyRef("parent_image_uri")
    confidence: PropertyRef = PropertyRef("confidence")


@dataclass(frozen=True)
class GitHubContainerImageToParentImageRel(CartographyRelSchema):
    """
    Relationship from a GitHubContainerImage to its parent/base image.
    """

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("parent_image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_FROM"
    properties: GitHubContainerImageToParentImageRelProperties = (
        GitHubContainerImageToParentImageRelProperties()
    )


@dataclass(frozen=True)
class GitHubContainerImageToPackageRel(CartographyRelSchema):
    """
    Links a container image to the package (registry repository) that hosts it.
    """

    target_node_label: str = "GitHubPackage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("package_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_IMAGE"
    properties: GitHubContainerImageRelProperties = GitHubContainerImageRelProperties()


@dataclass(frozen=True)
class GitHubContainerImageSchema(CartographyNodeSchema):
    """
    Schema for GitHub Container Image nodes.

    Relationships:
    - RESOURCE: Sub-resource to GitHubOrganization for cleanup
    - CONTAINS_IMAGE: From manifest lists to platform-specific images
    - HAS_LAYER / HEAD / TAIL: Image layer structure
    - BUILT_FROM: Parent/base image
    - HAS_IMAGE: Inverse of (GitHubPackage)-[:HAS_IMAGE]->(image)

    Extra labels:
    - Image: Applied to single image manifests (type="image")
    - ImageManifestList: Applied to manifest lists (type="manifest_list")
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
            GitHubContainerImageToPackageRel(),
            GitHubContainerImageContainsImageRel(),
            GitHubContainerImageToLayerRel(),
            GitHubContainerImageToHeadLayerRel(),
            GitHubContainerImageToTailLayerRel(),
            GitHubContainerImageToParentImageRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            ConditionalNodeLabel(
                label="Image",
                conditions={"type": "image"},
            ),
            ConditionalNodeLabel(
                label="ImageManifestList",
                conditions={"type": "manifest_list"},
            ),
        ],
    )


@dataclass(frozen=True)
class GitHubContainerImageProvenanceNodeProperties(CartographyNodeProperties):
    """
    Minimal property set for provenance-only updates on existing
    GitHubContainerImage nodes. Used by the attestation enrichment step so
    base manifest fields don't get nulled out on re-load.
    """

    id: PropertyRef = PropertyRef("digest")
    source_uri: PropertyRef = PropertyRef("source_uri", extra_index=True)
    source_revision: PropertyRef = PropertyRef("source_revision")
    source_file: PropertyRef = PropertyRef("source_file")
    parent_image_uri: PropertyRef = PropertyRef("parent_image_uri")
    parent_image_digest: PropertyRef = PropertyRef("parent_image_digest")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GitHubContainerImageProvenanceSchema(CartographyNodeSchema):
    """
    Schema for provenance-only enrichment of GitHubContainerImage nodes.
    """

    label: str = "GitHubContainerImage"
    properties: GitHubContainerImageProvenanceNodeProperties = (
        GitHubContainerImageProvenanceNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [GitHubContainerImageToParentImageRel()],
    )
