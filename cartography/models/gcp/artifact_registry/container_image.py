# DEPRECATED: This module is kept as a compatibility shim for the old
# GCPArtifactRegistryContainerImage model name and will be removed in v1.0.0.
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageProvenanceNodeProperties,
)
from cartography.models.gcp.artifact_registry.image import (
    GCPArtifactRegistryImageProvenanceSchema,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryProjectToRepositoryImageRel,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageMatchLinkProperties,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageNodeProperties,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageSchema,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageToProjectRel,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageToProjectRelProperties,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageToRepositoryRel,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryImageToRepositoryRelProperties,
)
from cartography.models.gcp.artifact_registry.repository_image import (
    GCPArtifactRegistryRepositoryToRepositoryImageRel,
)

GCPArtifactRegistryContainerImageMatchLinkProperties = (
    GCPArtifactRegistryRepositoryImageMatchLinkProperties
)
GCPArtifactRegistryContainerImageNodeProperties = (
    GCPArtifactRegistryRepositoryImageNodeProperties
)
GCPArtifactRegistryContainerImageSchema = GCPArtifactRegistryRepositoryImageSchema
GCPArtifactRegistryContainerImageToProjectRel = (
    GCPArtifactRegistryRepositoryImageToProjectRel
)
GCPArtifactRegistryContainerImageToProjectRelProperties = (
    GCPArtifactRegistryRepositoryImageToProjectRelProperties
)
GCPArtifactRegistryContainerImageToRepositoryRel = (
    GCPArtifactRegistryRepositoryImageToRepositoryRel
)
GCPArtifactRegistryContainerImageToRepositoryRelProperties = (
    GCPArtifactRegistryRepositoryImageToRepositoryRelProperties
)
GCPArtifactRegistryProjectToContainerImageRel = (
    GCPArtifactRegistryProjectToRepositoryImageRel
)
GCPArtifactRegistryRepositoryToContainerImageRel = (
    GCPArtifactRegistryRepositoryToRepositoryImageRel
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
