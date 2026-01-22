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
class ECRImageNodeProperties(CartographyNodeProperties):
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
class ECRImageSchema(CartographyNodeSchema):
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
