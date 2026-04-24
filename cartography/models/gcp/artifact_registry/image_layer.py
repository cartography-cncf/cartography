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
class GCPArtifactRegistryImageLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("diff_id")
    diff_id: PropertyRef = PropertyRef("diff_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    is_empty: PropertyRef = PropertyRef("is_empty")
    history: PropertyRef = PropertyRef("history")


@dataclass(frozen=True)
class GCPArtifactRegistryImageLayerToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageLayerToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryImageLayerToProjectRelProperties = (
        GCPArtifactRegistryImageLayerToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageLayerSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryImageLayer"
    properties: GCPArtifactRegistryImageLayerNodeProperties = (
        GCPArtifactRegistryImageLayerNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryImageLayerToProjectRel = (
        GCPArtifactRegistryImageLayerToProjectRel()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ImageLayer"])
