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
class GCPArtifactRegistryLanguagePackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    format: PropertyRef = PropertyRef("format")  # MAVEN, NPM, PYTHON, GO
    uri: PropertyRef = PropertyRef("uri")
    version: PropertyRef = PropertyRef("version")
    package_name: PropertyRef = PropertyRef("package_name")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)

    # Maven-specific properties (nullable for non-Maven)
    group_id: PropertyRef = PropertyRef("group_id")
    artifact_id: PropertyRef = PropertyRef("artifact_id")

    # NPM-specific properties (nullable for non-NPM)
    tags: PropertyRef = PropertyRef("tags")


@dataclass(frozen=True)
class GCPArtifactRegistryLanguagePackageToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryLanguagePackage)
class GCPArtifactRegistryLanguagePackageToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryLanguagePackageToProjectRelProperties = (
        GCPArtifactRegistryLanguagePackageToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryLanguagePackageToRepositoryRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryLanguagePackage)
class GCPArtifactRegistryLanguagePackageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryLanguagePackageToRepositoryRelProperties = (
        GCPArtifactRegistryLanguagePackageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryLanguagePackageSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryLanguagePackage"
    properties: GCPArtifactRegistryLanguagePackageNodeProperties = (
        GCPArtifactRegistryLanguagePackageNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryLanguagePackageToProjectRel = (
        GCPArtifactRegistryLanguagePackageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryLanguagePackageToRepositoryRel(),
        ]
    )
