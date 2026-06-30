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
class ScalewayContainerRegistryImageProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    status: PropertyRef = PropertyRef("status")
    status_message: PropertyRef = PropertyRef("status_message")
    # Per-image visibility (`public`, `private`, `inherit`). Combined with
    # the namespace `is_public`, drives the public-image exposure signal.
    visibility: PropertyRef = PropertyRef("visibility")
    size: PropertyRef = PropertyRef("size")
    tags: PropertyRef = PropertyRef("tags")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
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
class ScalewayContainerRegistryImageToNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayContainerRegistryNamespace)-[:HAS]->(:ScalewayContainerRegistryImage)
class ScalewayContainerRegistryImageToNamespaceRel(CartographyRelSchema):
    target_node_label: str = "ScalewayContainerRegistryNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("namespace_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS"
    properties: ScalewayContainerRegistryImageToNamespaceRelProperties = (
        ScalewayContainerRegistryImageToNamespaceRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryImageSchema(CartographyNodeSchema):
    label: str = "ScalewayContainerRegistryImage"
    properties: ScalewayContainerRegistryImageProperties = (
        ScalewayContainerRegistryImageProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryImageToProjectRel = (
        ScalewayContainerRegistryImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ScalewayContainerRegistryImageToNamespaceRel(),
        ]
    )
