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
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name assigned to this resource."
    )
    format: PropertyRef = PropertyRef(
        "format",
        description="Artifact Registry package format, such as DOCKER, MAVEN, NPM, PYTHON, APT, or YUM.",
    )  # MAVEN, NPM, PYTHON, GO
    uri: PropertyRef = PropertyRef(
        "uri",
        description="Artifact Registry URI used to retrieve this artifact or tagged image.",
    )
    version: PropertyRef = PropertyRef(
        "version",
        description="Artifact or chart version published in the repository.",
    )
    package_name: PropertyRef = PropertyRef(
        "package_name",
        description="Package coordinate or name within the repository.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when Google Cloud created this resource."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="Timestamp when Google Cloud last changed this resource.",
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

    # Maven-specific properties (nullable for non-Maven)
    group_id: PropertyRef = PropertyRef(
        "group_id",
        description="Maven group identifier when the artifact is a Maven package.",
    )
    artifact_id: PropertyRef = PropertyRef(
        "artifact_id",
        description="Maven artifact identifier when the artifact is a Maven package.",
    )

    # NPM-specific properties (nullable for non-NPM)
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Tag names associated with this artifact or image API record.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryLanguagePackageToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


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
    """A Google Cloud Artifact Registry Language Package resource."""

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
