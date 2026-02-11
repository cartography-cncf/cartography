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

    id: PropertyRef = PropertyRef("imageDigest")
    digest: PropertyRef = PropertyRef("imageDigest", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    type: PropertyRef = PropertyRef("type", extra_index=True)
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    variant: PropertyRef = PropertyRef("variant")
    attestation_type: PropertyRef = PropertyRef("attestation_type")
    attests_digest: PropertyRef = PropertyRef("attests_digest")
    media_type: PropertyRef = PropertyRef("media_type")
    artifact_media_type: PropertyRef = PropertyRef("artifact_media_type")
    child_image_digests: PropertyRef = PropertyRef("child_image_digests")


@dataclass(frozen=True)
class ECRImageNodeProperties(CartographyNodeProperties):
    """All ECRImage properties including layer/provenance fields managed by ecr_image_layers."""

    id: PropertyRef = PropertyRef("imageDigest")
    digest: PropertyRef = PropertyRef("imageDigest", extra_index=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")
    type: PropertyRef = PropertyRef("type", extra_index=True)
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    variant: PropertyRef = PropertyRef("variant")
    attestation_type: PropertyRef = PropertyRef("attestation_type")
    attests_digest: PropertyRef = PropertyRef("attests_digest")
    media_type: PropertyRef = PropertyRef("media_type")
    artifact_media_type: PropertyRef = PropertyRef("artifact_media_type")
    child_image_digests: PropertyRef = PropertyRef("child_image_digests")
    # SLSA Provenance: Source repository info from VCS metadata
    source_uri: PropertyRef = PropertyRef("source_uri", extra_index=True)
    source_revision: PropertyRef = PropertyRef("source_revision")
    # SLSA Provenance: Build invocation info from CI
    invocation_uri: PropertyRef = PropertyRef("invocation_uri", extra_index=True)
    invocation_workflow: PropertyRef = PropertyRef(
        "invocation_workflow", extra_index=True
    )
    invocation_run_number: PropertyRef = PropertyRef("invocation_run_number")
    # SLSA Provenance: Dockerfile path from configSource.entryPoint + vcs localdir
    source_file: PropertyRef = PropertyRef("source_file")


@dataclass(frozen=True)
class ECRImageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "ECRImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("layer_diff_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAYER"
    properties: ECRImageHasLayerRelProperties = ECRImageHasLayerRelProperties()


@dataclass(frozen=True)
class ECRImageToParentImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    from_attestation: PropertyRef = PropertyRef("from_attestation")
    parent_image_uri: PropertyRef = PropertyRef("parent_image_uri")
    confidence: PropertyRef = PropertyRef("confidence")


@dataclass(frozen=True)
class ECRImageToParentImageRel(CartographyRelSchema):
    """
    Relationship from an ECRImage to its parent ECRImage (BUILT_FROM).
    This relationship is created when provenance attestations explicitly specify the parent image.
    """

    target_node_label: str = "ECRImage"
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
    Relationship from a manifest list ECRImage to platform-specific ECRImages it contains.
    Only applies to ECRImage nodes with type="manifest_list".
    """

    target_node_label: str = "ECRImage"
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
    Relationship from an attestation ECRImage to the ECRImage it attests/validates.
    Only applies to ECRImage nodes with type="attestation".
    """

    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("attests_digest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ATTESTS"
    properties: ECRImageAttestsRelProperties = ECRImageAttestsRelProperties()


@dataclass(frozen=True)
class ECRImageBaseSchema(CartographyNodeSchema):
    """Schema used by the basic ECR module (ecr.py) to load image metadata from DescribeImages.

    Only includes properties from the ECR API — does NOT include layer or provenance
    fields (layer_diff_ids, source_uri, invocation_uri, etc.) so that loading from
    DescribeImages doesn't clear values set by ecr_image_layers.
    """

    label: str = "ECRImage"
    properties: ECRImageBaseNodeProperties = ECRImageBaseNodeProperties()
    sub_resource_relationship: ECRImageToAWSAccountRel = ECRImageToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRImageContainsImageRel(),
            ECRImageAttestsRel(),
        ],
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
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
    """Full schema used by ecr_image_layers to enrich ECRImage nodes with layer and provenance data.

    Also used for cleanup in ecr.py to handle all relationship types (HAS_LAYER, BUILT_FROM, etc.).
    """

    label: str = "ECRImage"
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
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
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
