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
class ImageLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("diff_id")
    diff_id: PropertyRef = PropertyRef("diff_id")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ImageLayerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ImageLayerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ImageLayerToAWSAccountRelProperties = (
        ImageLayerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ImageLayerToNextRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ImageLayerToNextRel(CartographyRelSchema):
    target_node_label: str = "ImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("next_diff_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NEXT"
    properties: ImageLayerToNextRelProperties = ImageLayerToNextRelProperties()


@dataclass(frozen=True)
class ImageLayerHeadOfImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ImageLayerHeadOfImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("head_image_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HEAD"
    properties: ImageLayerHeadOfImageRelProperties = (
        ImageLayerHeadOfImageRelProperties()
    )


@dataclass(frozen=True)
class ImageLayerTailOfImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ImageLayerTailOfImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tail_image_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAIL"
    properties: ImageLayerTailOfImageRelProperties = (
        ImageLayerTailOfImageRelProperties()
    )


@dataclass(frozen=True)
class ImageLayerSchema(CartographyNodeSchema):
    label: str = "ImageLayer"
    properties: ImageLayerNodeProperties = ImageLayerNodeProperties()
    sub_resource_relationship: ImageLayerToAWSAccountRel = ImageLayerToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ImageLayerToNextRel(),
            ImageLayerHeadOfImageRel(),
            ImageLayerTailOfImageRel(),
        ]
    )
