from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ConditionalNodeLabel
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
class GCPArtifactRegistryContainerImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    uri: PropertyRef = PropertyRef("uri", extra_index=True)
    digest: PropertyRef = PropertyRef("digest")
    tags: PropertyRef = PropertyRef("tags")
    image_size_bytes: PropertyRef = PropertyRef("image_size_bytes")
    media_type: PropertyRef = PropertyRef("media_type")
    upload_time: PropertyRef = PropertyRef("upload_time")
    build_time: PropertyRef = PropertyRef("build_time")
    update_time: PropertyRef = PropertyRef("update_time")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryContainerImageToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPProject)-[:RESOURCE]->(:GCPArtifactRegistryContainerImage)
class GCPArtifactRegistryContainerImageToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryContainerImageToProjectRelProperties = (
        GCPArtifactRegistryContainerImageToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryContainerImageToRepositoryRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:GCPArtifactRegistryRepository)-[:CONTAINS]->(:GCPArtifactRegistryContainerImage)
class GCPArtifactRegistryContainerImageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryContainerImageToRepositoryRelProperties = (
        GCPArtifactRegistryContainerImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryContainerImageMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
# Mirrors GCPArtifactRegistryContainerImageToProjectRel for relationship-only writes.
# Keep the relationship shape in sync.
class GCPArtifactRegistryProjectToContainerImageRel(CartographyRelSchema):
    source_node_label: str = "GCPProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryContainerImageMatchLinkProperties = (
        GCPArtifactRegistryContainerImageMatchLinkProperties()
    )


@dataclass(frozen=True)
# Mirrors GCPArtifactRegistryContainerImageToRepositoryRel for relationship-only writes.
# Keep the relationship shape in sync.
class GCPArtifactRegistryRepositoryToContainerImageRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryRepository"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryContainerImageMatchLinkProperties = (
        GCPArtifactRegistryContainerImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryContainerImageSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryContainerImage"
    properties: GCPArtifactRegistryContainerImageNodeProperties = (
        GCPArtifactRegistryContainerImageNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryContainerImageToProjectRel = (
        GCPArtifactRegistryContainerImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryContainerImageToRepositoryRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        [
            # Docker V2 manifest list (multi-arch)
            ConditionalNodeLabel(
                label="ImageManifestList",
                conditions={
                    "media_type": "application/vnd.docker.distribution.manifest.list.v2+json"
                },
            ),
            # OCI image index (multi-arch)
            ConditionalNodeLabel(
                label="ImageManifestList",
                conditions={"media_type": "application/vnd.oci.image.index.v1+json"},
            ),
            # Docker V2 manifest (single image)
            ConditionalNodeLabel(
                label="Image",
                conditions={
                    "media_type": "application/vnd.docker.distribution.manifest.v2+json"
                },
            ),
            # OCI image manifest (single image)
            ConditionalNodeLabel(
                label="Image",
                conditions={"media_type": "application/vnd.oci.image.manifest.v1+json"},
            ),
        ],
    )


@dataclass(frozen=True)
class GCPArtifactRegistryContainerImageProvenanceNodeProperties(
    CartographyNodeProperties,
):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    architecture: PropertyRef = PropertyRef("architecture")
    os: PropertyRef = PropertyRef("os")
    variant: PropertyRef = PropertyRef("variant")
    source_uri: PropertyRef = PropertyRef("source_uri", extra_index=True)
    source_revision: PropertyRef = PropertyRef("source_revision")
    source_file: PropertyRef = PropertyRef("source_file")
    layer_diff_ids: PropertyRef = PropertyRef("layer_diff_ids")


@dataclass(frozen=True)
class GCPArtifactRegistryContainerImageProvenanceSchema(CartographyNodeSchema):
    """Enrichment-only schema for updating GCP container images with provenance and layer data.

    Separate from the base schema so that basic API loads don't null out
    provenance fields set by the supply chain module (same pattern as ECR).
    """

    label: str = "GCPArtifactRegistryContainerImage"
    properties: GCPArtifactRegistryContainerImageProvenanceNodeProperties = (
        GCPArtifactRegistryContainerImageProvenanceNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryContainerImageToProjectRel = (
        GCPArtifactRegistryContainerImageToProjectRel()
    )
