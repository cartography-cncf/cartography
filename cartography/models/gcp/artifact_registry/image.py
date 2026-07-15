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
    id: PropertyRef = PropertyRef(
        "digest", description="Immutable OCI content digest used as the node ID."
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Digest that identifies the immutable artifact or image content.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="OCI content classification derived from manifest and artifact metadata.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description="OCI media type describing the manifest or artifact payload.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageManifestChildNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "digest", description="Immutable OCI content digest used as the node ID."
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Digest that identifies the immutable artifact or image content.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="OCI content classification derived from manifest and artifact metadata.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description="OCI media type describing the manifest or artifact payload.",
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="CPU architecture declared by the OCI image configuration.",
    )
    os: PropertyRef = PropertyRef(
        "os", description="Operating system declared by the OCI image configuration."
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version declared by the OCI image configuration.",
    )
    os_features: PropertyRef = PropertyRef(
        "os_features",
        description="Operating system feature list declared by the OCI platform metadata.",
    )
    variant: PropertyRef = PropertyRef(
        "variant",
        description="CPU architecture variant declared by the OCI platform metadata.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageProvenanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "digest", description="Immutable OCI content digest used as the node ID."
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Digest that identifies the immutable artifact or image content.",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description="OCI content classification derived from manifest and artifact metadata.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description="OCI media type describing the manifest or artifact payload.",
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="CPU architecture declared by the OCI image configuration.",
    )
    os: PropertyRef = PropertyRef(
        "os", description="Operating system declared by the OCI image configuration."
    )
    os_version: PropertyRef = PropertyRef(
        "os_version",
        description="Operating system version declared by the OCI image configuration.",
    )
    os_features: PropertyRef = PropertyRef(
        "os_features",
        description="Operating system feature list declared by the OCI platform metadata.",
    )
    variant: PropertyRef = PropertyRef(
        "variant",
        description="CPU architecture variant declared by the OCI platform metadata.",
    )
    source_uri: PropertyRef = PropertyRef(
        "source_uri",
        extra_index=True,
        description="Source repository URI extracted from verified build provenance or SPDX SBOM data.",
    )
    source_revision: PropertyRef = PropertyRef(
        "source_revision",
        description="Source revision extracted from verified build provenance or SPDX SBOM data.",
    )
    source_file: PropertyRef = PropertyRef(
        "source_file",
        description="Source file path extracted from verified build provenance or SPDX SBOM data.",
    )
    parent_image_uri: PropertyRef = PropertyRef(
        "parent_image_uri",
        description="Parent image URI extracted from a digest-verified SPDX SBOM relationship.",
    )
    parent_image_digest: PropertyRef = PropertyRef(
        "parent_image_digest",
        description="Immutable parent image digest extracted from a digest-verified SPDX SBOM relationship.",
    )
    layer_diff_ids: PropertyRef = PropertyRef(
        "layer_diff_ids",
        description="Ordered uncompressed layer digests from the OCI image configuration.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageBuiltFromRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )
    parent_image_uri: PropertyRef = PropertyRef(
        "parent_image_uri",
        description="Parent image URI extracted from a digest-verified SPDX SBOM relationship.",
    )
    from_sbom: PropertyRef = PropertyRef(
        "from_sbom",
        description=(
            "Match-method flag set when parent-image evidence comes from a "
            "digest-verified SPDX SBOM relationship."
        ),
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Parent-image evidence strength; digest-verified SBOM matches use `explicit`.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageBuiltFromMatchLink(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"digest": PropertyRef("digest")}
    )
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("parent_image_digest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_FROM"
    properties: GCPArtifactRegistryImageBuiltFromRelProperties = (
        GCPArtifactRegistryImageBuiltFromRelProperties()
    )


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
    """A Google Cloud Artifact Registry Image resource."""

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
class GCPArtifactRegistryImageManifestChildSchema(CartographyNodeSchema):
    """A Google Cloud Artifact Registry Image resource."""

    label: str = "GCPArtifactRegistryImage"
    properties: GCPArtifactRegistryImageManifestChildNodeProperties = (
        GCPArtifactRegistryImageManifestChildNodeProperties()
    )
    scoped_cleanup: bool = True
    other_relationships: OtherRelationships = OtherRelationships(
        [GCPArtifactRegistryImageContainsImageRel()],
    )
    extra_node_labels: ExtraNodeLabels = GCP_IMAGE_EXTRA_LABELS


@dataclass(frozen=True)
class GCPArtifactRegistryImageProvenanceSchema(CartographyNodeSchema):
    """A Google Cloud Artifact Registry Image resource."""

    label: str = "GCPArtifactRegistryImage"
    properties: GCPArtifactRegistryImageProvenanceNodeProperties = (
        GCPArtifactRegistryImageProvenanceNodeProperties()
    )
    scoped_cleanup: bool = True
    extra_node_labels: ExtraNodeLabels = GCP_IMAGE_EXTRA_LABELS
