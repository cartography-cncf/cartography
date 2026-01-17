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
class GCPArtifactRegistryDockerImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    uri: PropertyRef = PropertyRef("uri")
    digest: PropertyRef = PropertyRef("digest")
    tags: PropertyRef = PropertyRef("tags")
    image_size_bytes: PropertyRef = PropertyRef("image_size_bytes")
    media_type: PropertyRef = PropertyRef("media_type")
    upload_time: PropertyRef = PropertyRef("upload_time")
    build_time: PropertyRef = PropertyRef("build_time")
    update_time: PropertyRef = PropertyRef("update_time")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryDockerImageToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryDockerImage)
class GCPArtifactRegistryDockerImageToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryDockerImageToProjectRelProperties = (
        GCPArtifactRegistryDockerImageToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryDockerImageToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryDockerImage)
class GCPArtifactRegistryDockerImageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryDockerImageToRepositoryRelProperties = (
        GCPArtifactRegistryDockerImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryDockerImageSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryDockerImage"
    properties: GCPArtifactRegistryDockerImageNodeProperties = (
        GCPArtifactRegistryDockerImageNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryDockerImageToProjectRel = (
        GCPArtifactRegistryDockerImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryDockerImageToRepositoryRel(),
        ]
    )
