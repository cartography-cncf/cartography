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
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name assigned to this resource."
    )
    format: PropertyRef = PropertyRef(
        "format",
        description="Artifact Registry package format, such as DOCKER, MAVEN, NPM, PYTHON, APT, or YUM.",
    )  # APT or YUM
    package_name: PropertyRef = PropertyRef(
        "package_name",
        description="Package coordinate or name within the repository.",
    )
    repository_id: PropertyRef = PropertyRef(
        "repository_id",
        description="Full resource name of the containing Artifact Registry repository.",
    )
    project_id: PropertyRef = PropertyRef(
        "project_id", description="Google Cloud project that owns this resource."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryGenericArtifactToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """A Google Cloud Artifact Registry Generic Artifact resource."""

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
