from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPArtifactRegistryImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    type: PropertyRef = PropertyRef("type", extra_index=True)
    media_type: PropertyRef = PropertyRef("media_type")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    type: PropertyRef = PropertyRef("type", extra_index=True)
    media_type: PropertyRef = PropertyRef("media_type")
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    os_features: PropertyRef = PropertyRef("os_features")
    variant: PropertyRef = PropertyRef("variant")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageProvenanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    type: PropertyRef = PropertyRef("type", extra_index=True)
    media_type: PropertyRef = PropertyRef("media_type")
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    os_features: PropertyRef = PropertyRef("os_features")
    variant: PropertyRef = PropertyRef("variant")
    source_uri: PropertyRef = PropertyRef("source_uri", extra_index=True)
    source_revision: PropertyRef = PropertyRef("source_revision")
    source_file: PropertyRef = PropertyRef("source_file")
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageContainsImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("child_image_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GCPArtifactRegistryImageRelProperties = (
        GCPArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageContainsImageMatchLink(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"digest": PropertyRef("parent_digest")}
    )
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("child_digest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GCPArtifactRegistryImageMatchLinkProperties = (
        GCPArtifactRegistryImageMatchLinkProperties()
    )


GCP_IMAGE_EXTRA_LABELS = ExtraNodeLabels(
    [
        ConditionalNodeLabel(label="Image", conditions={"type": "image"}),
        ConditionalNodeLabel(
            label="ImageAttestation",
            conditions={"type": "attestation"},
        ),
        ConditionalNodeLabel(
            label="ImageManifestList",
            conditions={"type": "manifest_list"},
        ),
    ],
)


@dataclass(frozen=True)
class GCPArtifactRegistryImageSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryImage"
    properties: GCPArtifactRegistryImageNodeProperties = (
        GCPArtifactRegistryImageNodeProperties()
    )
    scoped_cleanup: bool = True
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPArtifactRegistryImageContainsImageRel()],
    )
    extra_node_labels: ExtraNodeLabels = GCP_IMAGE_EXTRA_LABELS


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageCompatSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryImage"
    properties: GCPArtifactRegistryPlatformImageNodeProperties = (
        GCPArtifactRegistryPlatformImageNodeProperties()
    )
    scoped_cleanup: bool = True
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPArtifactRegistryImageContainsImageRel()],
    )
    # DEPRECATED: GCPArtifactRegistryPlatformImage compatibility label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "GCPArtifactRegistryPlatformImage",
            ConditionalNodeLabel(label="Image", conditions={"type": "image"}),
            ConditionalNodeLabel(
                label="ImageAttestation",
                conditions={"type": "attestation"},
            ),
            ConditionalNodeLabel(
                label="ImageManifestList",
                conditions={"type": "manifest_list"},
            ),
        ],
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageProvenanceSchema(CartographyNodeSchema):
    """Enrichment-only schema for updating canonical GAR images with provenance and layer data."""

    label: str = "GCPArtifactRegistryImage"
    properties: GCPArtifactRegistryImageProvenanceNodeProperties = (
        GCPArtifactRegistryImageProvenanceNodeProperties()
    )
    scoped_cleanup: bool = True
    extra_node_labels: ExtraNodeLabels = GCP_IMAGE_EXTRA_LABELS
