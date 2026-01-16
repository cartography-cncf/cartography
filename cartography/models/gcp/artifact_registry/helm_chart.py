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
class GCPArtifactRegistryHelmChartNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    uri: PropertyRef = PropertyRef("uri")
    version: PropertyRef = PropertyRef("version")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryHelmChartToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryHelmChart)
class GCPArtifactRegistryHelmChartToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryHelmChartToProjectRelProperties = (
        GCPArtifactRegistryHelmChartToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryHelmChartToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryHelmChart)
class GCPArtifactRegistryHelmChartToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryHelmChartToRepositoryRelProperties = (
        GCPArtifactRegistryHelmChartToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryHelmChartSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryHelmChart"
    properties: GCPArtifactRegistryHelmChartNodeProperties = (
        GCPArtifactRegistryHelmChartNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryHelmChartToProjectRel = (
        GCPArtifactRegistryHelmChartToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryHelmChartToRepositoryRel(),
        ]
    )
