# DEPRECATED: This module is kept as a compatibility shim for the old
# GCPArtifactRegistryContainerImage model name and will be removed in v1.0.0.
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageProvenanceNodeProperties,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageProvenanceSchema,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefMatchLinkProperties,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefNodeProperties,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefSchema,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefToProjectRel,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefToProjectRelProperties,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefToRepositoryRel,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryImageRefToRepositoryRelProperties,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryProjectToImageRefRel,
)
from cartography.models.gcp.artifact_registry.image_ref import (
    GCPArtifactRegistryRepositoryToImageRefRel,
)

GCPArtifactRegistryContainerImageMatchLinkProperties = (
    GCPArtifactRegistryImageRefMatchLinkProperties
)
GCPArtifactRegistryContainerImageNodeProperties = (
    GCPArtifactRegistryImageRefNodeProperties
)
GCPArtifactRegistryContainerImageSchema = GCPArtifactRegistryImageRefSchema
GCPArtifactRegistryContainerImageToProjectRel = GCPArtifactRegistryImageRefToProjectRel
GCPArtifactRegistryContainerImageToProjectRelProperties = (
    GCPArtifactRegistryImageRefToProjectRelProperties
)
GCPArtifactRegistryContainerImageToRepositoryRel = (
    GCPArtifactRegistryImageRefToRepositoryRel
)
GCPArtifactRegistryContainerImageToRepositoryRelProperties = (
    GCPArtifactRegistryImageRefToRepositoryRelProperties
)
GCPArtifactRegistryProjectToContainerImageRel = GCPArtifactRegistryProjectToImageRefRel
GCPArtifactRegistryRepositoryToContainerImageRel = (
    GCPArtifactRegistryRepositoryToImageRefRel
)
GCPArtifactRegistryContainerImageProvenanceNodeProperties = (
    GCPArtifactRegistryImageProvenanceNodeProperties
)
GCPArtifactRegistryContainerImageProvenanceSchema = (
    GCPArtifactRegistryImageProvenanceSchema
)

__all__ = [
    "GCPArtifactRegistryContainerImageMatchLinkProperties",
    "GCPArtifactRegistryContainerImageNodeProperties",
    "GCPArtifactRegistryContainerImageProvenanceNodeProperties",
    "GCPArtifactRegistryContainerImageProvenanceSchema",
    "GCPArtifactRegistryContainerImageSchema",
    "GCPArtifactRegistryContainerImageToProjectRel",
    "GCPArtifactRegistryContainerImageToProjectRelProperties",
    "GCPArtifactRegistryContainerImageToRepositoryRel",
    "GCPArtifactRegistryContainerImageToRepositoryRelProperties",
    "GCPArtifactRegistryProjectToContainerImageRel",
    "GCPArtifactRegistryRepositoryToContainerImageRel",
]
