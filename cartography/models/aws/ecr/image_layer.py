from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_ECR_IMAGE_LAYER
from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import IMAGE_LAYER


@dataclass(frozen=True)
class ECRImageLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("diff_id", description="Same as `diff_id`")
    diff_id: PropertyRef = PropertyRef("diff_id", description="Digest of the layer")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_empty: PropertyRef = PropertyRef(
        "is_empty",
        description="Boolean flag identifying Docker's empty layer (true when the **DiffID** is `sha256:5f70bf18...`).",
    )
    history: PropertyRef = PropertyRef(
        "history",
        description="The `created_by` command from the image config that created this layer (e.g., `/bin/sh -c pip install flask`). Used for Dockerfile matching.",
    )


@dataclass(frozen=True)
class ECRImageLayerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageLayerToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECRImageLayerToAWSAccountRelProperties = (
        ECRImageLayerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECRImageLayerToNextRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageLayerToNextRel(CartographyRelSchema):
    target_node_label: str = "AWSECRImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("next_diff_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NEXT"
    properties: ECRImageLayerToNextRelProperties = ECRImageLayerToNextRelProperties()


@dataclass(frozen=True)
class ECRImageLayerHeadOfImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageLayerHeadOfImageRel(CartographyRelSchema):
    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("head_image_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HEAD"
    properties: ECRImageLayerHeadOfImageRelProperties = (
        ECRImageLayerHeadOfImageRelProperties()
    )


@dataclass(frozen=True)
class ECRImageLayerTailOfImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageLayerTailOfImageRel(CartographyRelSchema):
    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tail_image_ids", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "TAIL"
    properties: ECRImageLayerTailOfImageRelProperties = (
        ECRImageLayerTailOfImageRelProperties()
    )


@dataclass(frozen=True)
class ECRImageLayerSchema(CartographyNodeSchema):
    """Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `AWSECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)"""

    label: str = "AWSECRImageLayer"
    properties: ECRImageLayerNodeProperties = ECRImageLayerNodeProperties()
    sub_resource_relationship: ECRImageLayerToAWSAccountRel = (
        ECRImageLayerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRImageLayerToNextRel(),
            ECRImageLayerHeadOfImageRel(),
            ECRImageLayerTailOfImageRel(),
        ]
    )
    # DEPRECATED: legacy ECRImageLayer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_ECR_IMAGE_LAYER, IMAGE_LAYER]
    )


@dataclass(frozen=True)
class ECRImageLayerNodeSchema(CartographyNodeSchema):
    """Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `AWSECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)"""

    # Implementation note:
    # Load AWSECRImageLayer nodes without high-fanout one-to-many relationships.

    label: str = "AWSECRImageLayer"
    properties: ECRImageLayerNodeProperties = ECRImageLayerNodeProperties()
    sub_resource_relationship: ECRImageLayerToAWSAccountRel = (
        ECRImageLayerToAWSAccountRel()
    )
    # DEPRECATED: legacy ECRImageLayer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [LEGACY_ECR_IMAGE_LAYER, IMAGE_LAYER]
    )


@dataclass(frozen=True)
class ECRImageLayerRelLoadProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("diff_id", description="Same as `diff_id`")
    diff_id: PropertyRef = PropertyRef("diff_id", description="Digest of the layer")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRImageLayerNextRelSchema(CartographyNodeSchema):
    """Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `AWSECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)"""

    # Implementation note:
    # Load bounded NEXT relationship rows without reloading layer metadata.

    label: str = "AWSECRImageLayer"
    # DEPRECATED: legacy ECRImageLayer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_ECR_IMAGE_LAYER])
    properties: ECRImageLayerRelLoadProperties = ECRImageLayerRelLoadProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [ECRImageLayerToNextRel()],
    )


@dataclass(frozen=True)
class ECRImageLayerHeadRelSchema(CartographyNodeSchema):
    """Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `AWSECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)"""

    # Implementation note:
    # Load bounded HEAD relationship rows without reloading layer metadata.

    label: str = "AWSECRImageLayer"
    # DEPRECATED: legacy ECRImageLayer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_ECR_IMAGE_LAYER])
    properties: ECRImageLayerRelLoadProperties = ECRImageLayerRelLoadProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [ECRImageLayerHeadOfImageRel()],
    )


@dataclass(frozen=True)
class ECRImageLayerTailRelSchema(CartographyNodeSchema):
    """Representation of an individual Docker image layer discovered while processing ECR manifests. Layers are de-duplicated by `diff_id`, so multiple images (or multiple points within the same image) may reference the same `AWSECRImageLayer` node. Note that `diff_id` is the **uncompressed** (DiffID) SHA-256 of the layer tar stream. Docker's canonical empty layer therefore always appears as `sha256:5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef` and is marked with `is_empty = true`. (If you inspect registry manifests you may see the compressed blob digest `sha256:a3ed95ca...`, both refer to the same empty layer.)"""

    # Implementation note:
    # Load bounded TAIL relationship rows without reloading layer metadata.

    label: str = "AWSECRImageLayer"
    # DEPRECATED: legacy ECRImageLayer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([LEGACY_ECR_IMAGE_LAYER])
    properties: ECRImageLayerRelLoadProperties = ECRImageLayerRelLoadProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [ECRImageLayerTailOfImageRel()],
    )
