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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    format: PropertyRef = PropertyRef("format")
    mode: PropertyRef = PropertyRef("mode")
    description: PropertyRef = PropertyRef("description")
    location: PropertyRef = PropertyRef("location")
    registry_uri: PropertyRef = PropertyRef("registry_uri")
    size_bytes: PropertyRef = PropertyRef("size_bytes")
    kms_key_name: PropertyRef = PropertyRef("kms_key_name")
    create_time: PropertyRef = PropertyRef("create_time")
    update_time: PropertyRef = PropertyRef("update_time")
    cleanup_policy_dry_run: PropertyRef = PropertyRef("cleanup_policy_dry_run")
    vulnerability_scanning_enabled: PropertyRef = PropertyRef(
        "vulnerability_scanning_enabled"
    )
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPArtifactRegistryRepository"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ContainerRegistry"])
    properties: GCPArtifactRegistryRepositoryNodeProperties = (
        GCPArtifactRegistryRepositoryNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryRepositoryToProjectRel = (
        GCPArtifactRegistryRepositoryToProjectRel()
    )
