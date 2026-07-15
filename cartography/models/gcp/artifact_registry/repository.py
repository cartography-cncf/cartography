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
class GCPArtifactRegistryRepositoryNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", extra_index=True, description="Stable identifier for this resource."
    )
    name: PropertyRef = PropertyRef(
        "name", description="Name assigned to this resource."
    )
    format: PropertyRef = PropertyRef(
        "format",
        description="Artifact Registry package format, such as DOCKER, MAVEN, NPM, PYTHON, APT, or YUM.",
    )
    mode: PropertyRef = PropertyRef(
        "mode", description="Repository mode, such as standard, remote, or virtual."
    )
    description: PropertyRef = PropertyRef(
        "description", description="Description configured for this resource."
    )
    location: PropertyRef = PropertyRef(
        "location", description="Google Cloud location where this resource is deployed."
    )
    registry_uri: PropertyRef = PropertyRef(
        "registry_uri",
        description="Registry hostname and repository path used to address repository content.",
    )
    size_bytes: PropertyRef = PropertyRef(
        "size_bytes",
        description="Stored content size in bytes.",
    )
    kms_key_name: PropertyRef = PropertyRef(
        "kms_key_name",
        description="Cloud KMS key resource name used for repository encryption.",
    )
    create_time: PropertyRef = PropertyRef(
        "create_time", description="Timestamp when Google Cloud created this resource."
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="Timestamp when Google Cloud last changed this resource.",
    )
    cleanup_policy_dry_run: PropertyRef = PropertyRef(
        "cleanup_policy_dry_run",
        description="Whether cleanup policies are evaluated without deleting artifacts.",
    )
    vulnerability_scanning_enabled: PropertyRef = PropertyRef(
        "vulnerability_scanning_enabled",
        description="Whether Artifact Analysis vulnerability scanning is enabled for the repository.",
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
class GCPArtifactRegistryRepositoryToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryRepository)
class GCPArtifactRegistryRepositoryToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryRepositoryToProjectRelProperties = (
        GCPArtifactRegistryRepositoryToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositorySchema(CartographyNodeSchema):
    """A Google Cloud Artifact Registry Repository resource."""

    label: str = "GCPArtifactRegistryRepository"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: GCPArtifactRegistryRepositoryNodeProperties = (
        GCPArtifactRegistryRepositoryNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryRepositoryToProjectRel = (
        GCPArtifactRegistryRepositoryToProjectRel()
    )
