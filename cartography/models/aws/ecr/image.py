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
    digest: PropertyRef = PropertyRef("imageDigest")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")


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
class ECRImageSchema(CartographyNodeSchema):
    label: str = "ECRImage"
    properties: ECRImageNodeProperties = ECRImageNodeProperties()
    sub_resource_relationship: ECRImageToAWSAccountRel = ECRImageToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRImageHasLayerRel(),
            ECRImageToParentImageRel(),
        ],
    )
