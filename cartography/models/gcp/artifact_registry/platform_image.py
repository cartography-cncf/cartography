# DEPRECATED: This module is kept as a compatibility shim for the old
# GCPArtifactRegistryPlatformImage model name and will be removed in v1.0.0.
from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_source_node_matcher
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import SourceNodeMatcher
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageMatchLinkProperties,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryPlatformImageCompatSchema,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryPlatformImageNodeProperties as CanonicalPlatformImageNodeProperties,
)

GCPArtifactRegistryPlatformImageMatchLinkProperties = (
    GCPArtifactRegistryImageMatchLinkProperties
)
GCPArtifactRegistryPlatformImageNodeProperties = CanonicalPlatformImageNodeProperties
GCPArtifactRegistryPlatformImageSchema = GCPArtifactRegistryPlatformImageCompatSchema


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageToDockerImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_artifact_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_MANIFEST"
    properties: GCPArtifactRegistryPlatformImageMatchLinkProperties = (
        GCPArtifactRegistryPlatformImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryPlatformImageToParentImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("parent_artifact_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS_IMAGE"
    properties: GCPArtifactRegistryPlatformImageMatchLinkProperties = (
        GCPArtifactRegistryPlatformImageMatchLinkProperties()
    )


@dataclass(frozen=True)
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


__all__ = [
    "GCPArtifactRegistryContainerImageContainsPlatformImageRel",
    "GCPArtifactRegistryContainerImageToPlatformImageRel",
    "GCPArtifactRegistryPlatformImageMatchLinkProperties",
    "GCPArtifactRegistryPlatformImageNodeProperties",
    "GCPArtifactRegistryPlatformImageSchema",
    "GCPArtifactRegistryPlatformImageToDockerImageRel",
    "GCPArtifactRegistryPlatformImageToParentImageRel",
    "GCPArtifactRegistryProjectToPlatformImageRel",
]
