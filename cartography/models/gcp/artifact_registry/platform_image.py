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
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    digest: PropertyRef = PropertyRef("digest")
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    os_version: PropertyRef = PropertyRef("os_version")
    os_features: PropertyRef = PropertyRef("os_features")
    variant: PropertyRef = PropertyRef("variant")
    media_type: PropertyRef = PropertyRef("media_type")
    parent_artifact_id: PropertyRef = PropertyRef("parent_artifact_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryPlatformImage)
class GCPArtifactRegistryPlatformImageToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryPlatformImageToProjectRelProperties = (
        GCPArtifactRegistryPlatformImageToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageToArtifactRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryContainerImage)-[:HAS_MANIFEST]->(:GCPArtifactRegistryPlatformImage)
class GCPArtifactRegistryPlatformImageToDockerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_artifact_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_MANIFEST"
    properties: GCPArtifactRegistryPlatformImageToArtifactRelProperties = (
        GCPArtifactRegistryPlatformImageToArtifactRelProperties()
    )


@dataclass(frozen=True)
# (:GCPArtifactRegistryContainerImage)-[:CONTAINS_IMAGE]->(:GCPArtifactRegistryPlatformImage)
class GCPArtifactRegistryPlatformImageToParentImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_artifact_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GCPArtifactRegistryPlatformImageToArtifactRelProperties = (
        GCPArtifactRegistryPlatformImageToArtifactRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Mirrors GCPArtifactRegistryPlatformImageToProjectRel for relationship-only writes.
# Keep the relationship shape in sync.
class GCPArtifactRegistryProjectToPlatformImageRel(CartographyRelSchema):
    source_node_label: str = "GCPProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryPlatformImageMatchLinkProperties = (
        GCPArtifactRegistryPlatformImageMatchLinkProperties()
    )


@dataclass(frozen=True)
# Mirrors GCPArtifactRegistryPlatformImageToDockerImageRel for relationship-only writes.
# Keep the relationship shape in sync.
class GCPArtifactRegistryContainerImageToPlatformImageRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryContainerImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("parent_artifact_id")}
    )
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_MANIFEST"
    properties: GCPArtifactRegistryPlatformImageMatchLinkProperties = (
        GCPArtifactRegistryPlatformImageMatchLinkProperties()
    )


@dataclass(frozen=True)
# Mirrors GCPArtifactRegistryPlatformImageToParentImageRel for relationship-only writes.
# Keep the relationship shape in sync.
class GCPArtifactRegistryContainerImageContainsPlatformImageRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryContainerImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("parent_artifact_id")}
    )
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GCPArtifactRegistryPlatformImageMatchLinkProperties = (
        GCPArtifactRegistryPlatformImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryPlatformImage"
    properties: GCPArtifactRegistryPlatformImageNodeProperties = (
        GCPArtifactRegistryPlatformImageNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryPlatformImageToProjectRel = (
        GCPArtifactRegistryPlatformImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryPlatformImageToDockerImageRel(),
            GCPArtifactRegistryPlatformImageToParentImageRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Image"])
