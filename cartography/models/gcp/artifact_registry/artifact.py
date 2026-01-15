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
class GCPArtifactRegistryArtifactNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    format: PropertyRef = PropertyRef("format")
    uri: PropertyRef = PropertyRef("uri")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Docker-specific properties (nullable for non-Docker)
    digest: PropertyRef = PropertyRef("digest")
    tags: PropertyRef = PropertyRef("tags")
    image_size_bytes: PropertyRef = PropertyRef("image_size_bytes")
    media_type: PropertyRef = PropertyRef("media_type")
    artifact_type: PropertyRef = PropertyRef("artifact_type")
    upload_time: PropertyRef = PropertyRef("upload_time")
    build_time: PropertyRef = PropertyRef("build_time")

    # Package-specific properties (nullable for Docker)
    version: PropertyRef = PropertyRef("version")
    display_name: PropertyRef = PropertyRef("display_name")
    annotations: PropertyRef = PropertyRef("annotations")


@dataclass(frozen=True)
class GCPArtifactRegistryArtifactToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryArtifact)
class GCPArtifactRegistryArtifactToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryArtifactToProjectRelProperties = (
        GCPArtifactRegistryArtifactToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryArtifactToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryArtifact)
class GCPArtifactRegistryArtifactToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryArtifactToRepositoryRelProperties = (
        GCPArtifactRegistryArtifactToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryArtifactSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryArtifact"
    properties: GCPArtifactRegistryArtifactNodeProperties = (
        GCPArtifactRegistryArtifactNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryArtifactToProjectRel = (
        GCPArtifactRegistryArtifactToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryArtifactToRepositoryRel(),
        ]
    )
