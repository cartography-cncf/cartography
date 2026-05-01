from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPArtifactRegistryImageLayerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("diff_id")
    diff_id: PropertyRef = PropertyRef("diff_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
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
class GCPArtifactRegistryImageLayerMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Mirrors GCPArtifactRegistryImageLayerToProjectRel for relationship-only writes.
# Keep the relationship shape in sync.
class GCPArtifactRegistryProjectToImageLayerRel(CartographyRelSchema):
    source_node_label: str = "GCPProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    target_node_label: str = "GCPArtifactRegistryImageLayer"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("diff_id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryImageLayerMatchLinkProperties = (
        GCPArtifactRegistryImageLayerMatchLinkProperties()
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
