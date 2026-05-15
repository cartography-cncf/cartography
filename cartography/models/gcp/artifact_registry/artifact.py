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
class GCPArtifactRegistryGenericArtifactNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    format: PropertyRef = PropertyRef("format")  # APT or YUM
    package_name: PropertyRef = PropertyRef("package_name")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryGenericArtifactToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryGenericArtifact)
class GCPArtifactRegistryGenericArtifactToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryGenericArtifactToProjectRelProperties = (
        GCPArtifactRegistryGenericArtifactToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryGenericArtifactToRepositoryRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryGenericArtifact)
class GCPArtifactRegistryGenericArtifactToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryGenericArtifactToRepositoryRelProperties = (
        GCPArtifactRegistryGenericArtifactToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryGenericArtifactSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryGenericArtifact"
    properties: GCPArtifactRegistryGenericArtifactNodeProperties = (
        GCPArtifactRegistryGenericArtifactNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryGenericArtifactToProjectRel = (
        GCPArtifactRegistryGenericArtifactToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryGenericArtifactToRepositoryRel(),
        ]
    )
