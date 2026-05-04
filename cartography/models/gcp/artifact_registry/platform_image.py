# DEPRECATED: This module is kept as a compatibility shim for the old
# GCPArtifactRegistryPlatformImage model name and will be removed in v1.0.0.
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageContainsImageMatchLink,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageMatchLinkProperties,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryPlatformImageCompatSchema,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryPlatformImageNodeProperties as CanonicalPlatformImageNodeProperties,
)

GCPArtifactRegistryContainerImageContainsPlatformImageRel = (
    GCPArtifactRegistryImageContainsImageMatchLink
)
GCPArtifactRegistryContainerImageToPlatformImageRel = (
    GCPArtifactRegistryImageContainsImageMatchLink
)
GCPArtifactRegistryPlatformImageToDockerImageRel = (
    GCPArtifactRegistryImageContainsImageMatchLink
)
GCPArtifactRegistryPlatformImageToParentImageRel = (
    GCPArtifactRegistryImageContainsImageMatchLink
)
GCPArtifactRegistryPlatformImageMatchLinkProperties = (
    GCPArtifactRegistryImageMatchLinkProperties
)
GCPArtifactRegistryPlatformImageNodeProperties = CanonicalPlatformImageNodeProperties
GCPArtifactRegistryPlatformImageSchema = GCPArtifactRegistryPlatformImageCompatSchema
GCPArtifactRegistryProjectToPlatformImageRel = (
    GCPArtifactRegistryContainerImageToPlatformImageRel
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
