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
class ECRImageBaseNodeProperties(CartographyNodeProperties):
    """Properties managed by the basic ECR module (ecr.py) from DescribeImages API."""

    id: PropertyRef = PropertyRef("imageDigest", description="Same as digest")
    digest: PropertyRef = PropertyRef(
        "imageDigest", extra_index=True, description="The hash of this ECR image"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description='Type of image: `"image"` (platform-specific or single-arch image), `"manifest_list"` (multi-arch index), or `"attestation"` (attestation manifest)',
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description='CPU architecture (e.g., `"amd64"`, `"arm64"`). Set to `"unknown"` for attestations, `null` for manifest lists.',
    )
    os: PropertyRef = PropertyRef(
        "os",
        description='Operating system (e.g., `"linux"`, `"windows"`). Set to `"unknown"` for attestations, `null` for manifest lists.',
    )
    variant: PropertyRef = PropertyRef(
        "variant",
        description='Architecture variant (e.g., `"v8"` for ARM). Optional field.',
    )
    attestation_type: PropertyRef = PropertyRef(
        "attestation_type",
        description='For attestations only: the type of attestation (e.g., `"attestation-manifest"`). `null` for regular images.',
    )
    attests_digest: PropertyRef = PropertyRef(
        "attests_digest",
        description="For attestations only: the digest of the image this attestation is for. `null` for regular images.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description='The OCI/Docker media type of this manifest (e.g., `"application/vnd.oci.image.manifest.v1+json"`)',
    )
    artifact_media_type: PropertyRef = PropertyRef(
        "artifact_media_type",
        description="The artifact media type if this is an OCI artifact. Optional field.",
    )
    child_image_digests: PropertyRef = PropertyRef(
        "child_image_digests",
        description="For manifest lists only: list of platform-specific image digests contained in this manifest list. Excludes attestations. `null` for regular images and attestations.",
    )


@dataclass(frozen=True)
class ECRImageNodeProperties(CartographyNodeProperties):
    """All AWSECRImage properties including layer/provenance fields managed by ecr_image_layers."""

    id: PropertyRef = PropertyRef("imageDigest", description="Same as digest")
    digest: PropertyRef = PropertyRef(
        "imageDigest", extra_index=True, description="The hash of this ECR image"
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    layer_diff_ids: PropertyRef = PropertyRef(
        "layer_diff_ids",
        description='Ordered list of image layer digests for this image. Only set for `type="image"` nodes. `null` for manifest lists and attestations.',
    )
    type: PropertyRef = PropertyRef(
        "type",
        extra_index=True,
        description='Type of image: `"image"` (platform-specific or single-arch image), `"manifest_list"` (multi-arch index), or `"attestation"` (attestation manifest)',
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description='CPU architecture (e.g., `"amd64"`, `"arm64"`). Set to `"unknown"` for attestations, `null` for manifest lists.',
    )
    os: PropertyRef = PropertyRef(
        "os",
        description='Operating system (e.g., `"linux"`, `"windows"`). Set to `"unknown"` for attestations, `null` for manifest lists.',
    )
    variant: PropertyRef = PropertyRef(
        "variant",
        description='Architecture variant (e.g., `"v8"` for ARM). Optional field.',
    )
    attestation_type: PropertyRef = PropertyRef(
        "attestation_type",
        description='For attestations only: the type of attestation (e.g., `"attestation-manifest"`). `null` for regular images.',
    )
    attests_digest: PropertyRef = PropertyRef(
        "attests_digest",
        description="For attestations only: the digest of the image this attestation is for. `null` for regular images.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description='The OCI/Docker media type of this manifest (e.g., `"application/vnd.oci.image.manifest.v1+json"`)',
    )
    artifact_media_type: PropertyRef = PropertyRef(
        "artifact_media_type",
        description="The artifact media type if this is an OCI artifact. Optional field.",
    )
    child_image_digests: PropertyRef = PropertyRef(
        "child_image_digests",
        description="For manifest lists only: list of platform-specific image digests contained in this manifest list. Excludes attestations. `null` for regular images and attestations.",
    )
    # SLSA Provenance: Source repository info from VCS metadata
    source_uri: PropertyRef = PropertyRef(
        "source_uri",
        extra_index=True,
        description="Source repository URI extracted from SLSA provenance attestations (e.g., a GitLab project URL or GitHub repo URL). Indexed for cross-module matching.",
    )
    source_revision: PropertyRef = PropertyRef(
        "source_revision",
        description="Source commit revision from SLSA provenance attestations.",
    )
    # SLSA Provenance: Build invocation info from CI
    invocation_uri: PropertyRef = PropertyRef(
        "invocation_uri",
        extra_index=True,
        description="CI/CD invocation URI from SLSA provenance (e.g., GitHub repository URL). Indexed for cross-module matching.",
    )
    invocation_workflow: PropertyRef = PropertyRef(
        "invocation_workflow",
        extra_index=True,
        description="CI/CD workflow path from SLSA provenance (e.g., `.github/workflows/build.yml`). Indexed for cross-module matching.",
    )
    invocation_run_number: PropertyRef = PropertyRef(
        "invocation_run_number",
        description="CI/CD run number from SLSA provenance (e.g., the GitHub Actions run number).",
    )
    # SLSA Provenance: Dockerfile path from configSource.entryPoint + vcs localdir
    source_file: PropertyRef = PropertyRef(
        "source_file",
        description="Dockerfile path from SLSA provenance (`configSource.entryPoint` prefixed with `vcs localdir:dockerfile` if present).",
    )


@dataclass(frozen=True)
class ECRImageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECRImage`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECRImageToAWSAccountRelProperties = ECRImageToAWSAccountRelProperties()


@dataclass(frozen=True)
class ECRImageHasLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageHasLayerRel(CartographyRelSchema):
    "Represents a `HAS_LAYER` relationship from `AWSECRImage` to `AWSECRImageLayer`."

    target_node_label: str = "AWSECRImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("layer_diff_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAYER"
    properties: ECRImageHasLayerRelProperties = ECRImageHasLayerRelProperties()


@dataclass(frozen=True)
class ECRImageToParentImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    from_attestation: PropertyRef = PropertyRef(
        "from_attestation",
        description="Whether the parent image relationship was derived from a provenance attestation.",
    )
    parent_image_uri: PropertyRef = PropertyRef(
        "parent_image_uri",
        description="Container image URI identifying the parent image in this relationship.",
    )
    confidence: PropertyRef = PropertyRef(
        "confidence",
        description="Confidence level assigned to the inferred relationship.",
    )


@dataclass(frozen=True)
class ECRImageToParentImageRel(CartographyRelSchema):
    """
    Relationship from an AWSECRImage to its parent AWSECRImage (BUILT_FROM).
    This relationship is created when provenance attestations explicitly specify the parent image.
    """

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("parent_image_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BUILT_FROM"
    properties: ECRImageToParentImageRelProperties = (
        ECRImageToParentImageRelProperties()
    )


@dataclass(frozen=True)
class ECRImageContainsImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageContainsImageRel(CartographyRelSchema):
    """
    Relationship from a manifest list AWSECRImage to platform-specific ECRImages it contains.
    Only applies to AWSECRImage nodes with type="manifest_list".
    """

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("child_image_digests", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: ECRImageContainsImageRelProperties = (
        ECRImageContainsImageRelProperties()
    )


@dataclass(frozen=True)
class ECRImageAttestsRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageAttestsRel(CartographyRelSchema):
    """
    Relationship from an attestation AWSECRImage to the AWSECRImage it attests/validates.
    Only applies to AWSECRImage nodes with type="attestation".
    """

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("attests_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTESTS"
    properties: ECRImageAttestsRelProperties = ECRImageAttestsRelProperties()


@dataclass(frozen=True)
class ECRImageBaseSchema(CartographyNodeSchema):
    "Represents an image, manifest list, or attestation artifact stored in Amazon ECR."

    # Implementation note:
    # Schema used by the basic ECR module (ecr.py) to load image metadata from
    # DescribeImages.
    #
    # Only includes properties from the ECR API: does NOT include layer or provenance
    # fields (layer_diff_ids, source_uri, invocation_uri, etc.) so that loading from
    # DescribeImages doesn't clear values set by ecr_image_layers.

    label: str = "AWSECRImage"
    properties: ECRImageBaseNodeProperties = ECRImageBaseNodeProperties()
    sub_resource_relationship: ECRImageToAWSAccountRel = ECRImageToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRImageContainsImageRel(),
            ECRImageAttestsRel(),
        ],
    )
    # DEPRECATED: legacy ECRImage node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "ECRImage",
            ConditionalNodeLabel(
                label="Image",
                conditions={"type": "image"},
            ),
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
class ECRImageSchema(CartographyNodeSchema):
    "Represents an image, manifest list, or attestation artifact stored in Amazon ECR."

    # Implementation note:
    # Full schema used by ecr_image_layers to enrich AWSECRImage nodes with layer and
    # provenance data.
    #
    # Also used for cleanup in ecr.py to handle all relationship types (HAS_LAYER,
    # BUILT_FROM, etc.).

    label: str = "AWSECRImage"
    properties: ECRImageNodeProperties = ECRImageNodeProperties()
    sub_resource_relationship: ECRImageToAWSAccountRel = ECRImageToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRImageHasLayerRel(),
            ECRImageToParentImageRel(),
            ECRImageContainsImageRel(),
            ECRImageAttestsRel(),
        ],
    )
    # DEPRECATED: legacy ECRImage node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "ECRImage",
            ConditionalNodeLabel(
                label="Image",
                conditions={"type": "image"},
            ),
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
class ECRImageLayerEnrichmentSchema(CartographyNodeSchema):
    "Represents an image, manifest list, or attestation artifact stored in Amazon ECR."

    # Implementation note:
    # Load AWSECRImage layer/provenance properties without fan-out HAS_LAYER edges.

    label: str = "AWSECRImage"
    properties: ECRImageNodeProperties = ECRImageNodeProperties()
    sub_resource_relationship: ECRImageToAWSAccountRel = ECRImageToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRImageToParentImageRel(),
            ECRImageContainsImageRel(),
            ECRImageAttestsRel(),
        ],
    )
    # DEPRECATED: legacy ECRImage node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            "ECRImage",
            ConditionalNodeLabel(
                label="Image",
                conditions={"type": "image"},
            ),
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
class ECRImageHasLayerRelLoadProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("imageDigest", description="Same as digest")
    digest: PropertyRef = PropertyRef(
        "imageDigest", description="The hash of this ECR image"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECRImageHasLayerRelSchema(CartographyNodeSchema):
    "Represents an image, manifest list, or attestation artifact stored in Amazon ECR."

    # Implementation note:
    # Load bounded HAS_LAYER relationship rows without reloading image metadata.

    label: str = "AWSECRImage"
    # DEPRECATED: legacy ECRImage node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECRImage"])
    properties: ECRImageHasLayerRelLoadProperties = ECRImageHasLayerRelLoadProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [ECRImageHasLayerRel()],
    )
