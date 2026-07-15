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
class ScalewayContainerRegistryNamespaceProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name", extra_index=True)
    description: PropertyRef = PropertyRef("description")
    status: PropertyRef = PropertyRef("status")
    status_message: PropertyRef = PropertyRef("status_message")
    endpoint: PropertyRef = PropertyRef("endpoint", extra_index=True)
    # Exposure signal: a public namespace lets unauthenticated `docker pull`s
    # read every image in it.
    is_public: PropertyRef = PropertyRef("is_public")
    size: PropertyRef = PropertyRef("size")
    image_count: PropertyRef = PropertyRef("image_count")
    region: PropertyRef = PropertyRef("region")
    created_at: PropertyRef = PropertyRef("created_at")
    updated_at: PropertyRef = PropertyRef("updated_at")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ScalewayContainerRegistryNamespaceToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryNamespace)
class ScalewayContainerRegistryNamespaceToProjectRel(CartographyRelSchema):
    target_node_label: str = "ScalewayProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ScalewayContainerRegistryNamespaceToProjectRelProperties = (
        ScalewayContainerRegistryNamespaceToProjectRelProperties()
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryNamespaceSchema(CartographyNodeSchema):
    label: str = "ScalewayContainerRegistryNamespace"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: ScalewayContainerRegistryNamespaceProperties = (
        ScalewayContainerRegistryNamespaceProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryNamespaceToProjectRel = (
        ScalewayContainerRegistryNamespaceToProjectRel()
    )
