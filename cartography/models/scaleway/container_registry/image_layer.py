from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ScalewayContainerRegistryImageLayerNodeProperties(CartographyNodeProperties):
    # A filesystem layer, keyed by its uncompressed digest (diff_id). Shared
    # across images that reuse the same layer. `history` is the build command
    # (`created_by`) that produced it; the supply-chain dockerfile matcher
    # compares these against repository Dockerfiles.
    id: PropertyRef = PropertyRef("diff_id")
    diff_id: PropertyRef = PropertyRef("diff_id", extra_index=True)
    history: PropertyRef = PropertyRef("history")
    is_empty: PropertyRef = PropertyRef("is_empty")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayContainerRegistryImageLayerToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImageLayer)
class ScalewayContainerRegistryImageLayerToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayContainerRegistryImageLayerToProjectRelProperties = (
        ScalewayContainerRegistryImageLayerToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageLayerSchema(CartographyNodeSchema):
    label: str = "ScalewayContainerRegistryImageLayer"
    # `ImageLayer` is the cross-provider label the supply-chain dockerfile
    # matcher looks up by diff_id (mirrors ECRImageLayer / GCPArtifactRegistryImageLayer).
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ImageLayer"])
    properties: ScalewayContainerRegistryImageLayerNodeProperties = (
        ScalewayContainerRegistryImageLayerNodeProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryImageLayerToProjectRel = (
        ScalewayContainerRegistryImageLayerToProjectRel()
    )
