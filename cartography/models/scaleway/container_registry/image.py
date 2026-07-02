from dataclasses import dataclass

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


@dataclass(frozen=True)
class ScalewayContainerRegistryImageProperties(CartographyNodeProperties):
    # The digest-addressed image content. Scaleway's registry keys content by
    # digest (carried on tags); the "named image" from list_images is only a
    # repository grouping and is not modeled as its own node. Many tags (and
    # repositories) can reference the same digest, so this node is deduplicated
    # by digest.
    id: PropertyRef = PropertyRef("digest")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    # Ordered uncompressed layer digests, from the OCI image config; feeds the
    # supply-chain dockerfile matcher. Populated by the supply_chain enrichment.
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayContainerRegistryImageToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryImage)
class ScalewayContainerRegistryImageToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayContainerRegistryImageToProjectRelProperties = (
        ScalewayContainerRegistryImageToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageToLayerRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayContainerRegistryImage)-[:HAS_LAYER]->(:ScalewayContainerRegistryImageLayer)
class ScalewayContainerRegistryImageToLayerRel(CartographyRelSchema):
    target_node_label: str = "ScalewayContainerRegistryImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"diff_id": PropertyRef("layer_diff_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_LAYER"
    properties: ScalewayContainerRegistryImageToLayerRelProperties = (
        ScalewayContainerRegistryImageToLayerRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageSchema(CartographyNodeSchema):
    label: str = "ScalewayContainerRegistryImage"
    # Ontology `Image`: the digest-addressed content, the join target for
    # (:Container|:Function)-[:HAS_IMAGE]->(:Image) and RESOLVED_IMAGE.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Image"])
    properties: ScalewayContainerRegistryImageProperties = (
        ScalewayContainerRegistryImageProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryImageToProjectRel = (
        ScalewayContainerRegistryImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayContainerRegistryImageToLayerRel(),
        ]
    )
