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
    id: PropertyRef = PropertyRef("id", extra_index=True, description="Namespace UUID.")
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="Namespace name."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Namespace description."
    )
    status: PropertyRef = PropertyRef("status", description="Namespace status.")
    status_message: PropertyRef = PropertyRef(
        "status_message", description="Human-readable status message."
    )
    endpoint: PropertyRef = PropertyRef(
        "endpoint",
        extra_index=True,
        description="Registry endpoint (e.g. `rg.fr-par.scw.cloud/<name>`).",
    )
    # Exposure signal: a public namespace lets unauthenticated `docker pull`s
    # read every image in it.
    is_public: PropertyRef = PropertyRef(
        "is_public", description="True if the namespace allows unauthenticated reads."
    )
    size: PropertyRef = PropertyRef(
        "size", description="Total size in bytes of stored images."
    )
    image_count: PropertyRef = PropertyRef(
        "image_count", description="Number of images in the namespace."
    )
    region: PropertyRef = PropertyRef(
        "region", description="Region the namespace lives in."
    )
    created_at: PropertyRef = PropertyRef(
        "created_at", description="Creation timestamp."
    )
    updated_at: PropertyRef = PropertyRef(
        "updated_at", description="Last update timestamp."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated", set_in_kwargs=True, description="Timestamp of the last update"
    )


@dataclass(frozen=True)
class ScalewayContainerRegistryNamespaceToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:ScalewayProject)-[:RESOURCE]->(:ScalewayContainerRegistryNamespace)
class ScalewayContainerRegistryNamespaceToProjectRel(CartographyRelSchema):
    """Connects `ScalewayProject` to `ScalewayContainerRegistryNamespace` through
    `RESOURCE`.
    """

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
    """Represents a Scaleway Container Registry namespace (top-level repository scope)."""

    label: str = "ScalewayContainerRegistryNamespace"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: ScalewayContainerRegistryNamespaceProperties = (
        ScalewayContainerRegistryNamespaceProperties()
    )
    sub_resource_relationship: ScalewayContainerRegistryNamespaceToProjectRel = (
        ScalewayContainerRegistryNamespaceToProjectRel()
    )
