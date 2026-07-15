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
class GCPArtifactRegistryRepositoryImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        extra_index=True,
        description=(
            "Tag-scoped pull URI used as the node ID; untagged API records use "
            "their digest-pinned URI."
        ),
    )
    name: PropertyRef = PropertyRef(
        "name", description="Final segment of the DockerImage API resource name."
    )
    uri: PropertyRef = PropertyRef(
        "uri",
        extra_index=True,
        description="Artifact Registry URI used to retrieve this artifact or tagged image.",
    )
    _ont_uri: PropertyRef = PropertyRef(
        "uri", description="Normalized pull URI used by the ImageTag ontology."
    )
    digest: PropertyRef = PropertyRef(
        "digest",
        extra_index=True,
        description="Digest that identifies the immutable artifact or image content.",
    )
    tag: PropertyRef = PropertyRef(
        "tag", description="Tag represented by this repository-scoped image node."
    )
    _ont_tag: PropertyRef = PropertyRef(
        "tag", description="Normalized tag used by the ImageTag ontology."
    )
    tags: PropertyRef = PropertyRef(
        "tags",
        description="Tag names associated with this artifact or image API record.",
    )
    resource_name: PropertyRef = PropertyRef(
        "resource_name",
        extra_index=True,
        description="Artifact Registry DockerImage API resource name.",
    )
    digest_uri: PropertyRef = PropertyRef(
        "digest_uri",
        description="Pullable repository URI pinned to the immutable image digest.",
    )
    image_size_bytes: PropertyRef = PropertyRef(
        "image_size_bytes",
        description="Compressed image size reported by Artifact Registry, in bytes.",
    )
    media_type: PropertyRef = PropertyRef(
        "media_type",
        description="OCI media type describing the manifest or artifact payload.",
    )
    upload_time: PropertyRef = PropertyRef(
        "upload_time",
        description="Timestamp when the image was uploaded to Artifact Registry.",
    )
    build_time: PropertyRef = PropertyRef(
        "build_time",
        description="Timestamp when the image was built, when reported.",
    )
    update_time: PropertyRef = PropertyRef(
        "update_time",
        description="Timestamp when Google Cloud last changed this resource.",
    )
    artifact_type: PropertyRef = PropertyRef(
        "artifact_type",
        description="Artifact media type reported for the repository image.",
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


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryRepositoryImageToProjectRelProperties = (
        GCPArtifactRegistryRepositoryImageToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToRepositoryRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryRepositoryImageToRepositoryRelProperties = (
        GCPArtifactRegistryRepositoryImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToRepositoryRepoImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPO_IMAGE"
    properties: GCPArtifactRegistryRepositoryImageToRepositoryRelProperties = (
        GCPArtifactRegistryRepositoryImageToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("digest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: GCPArtifactRegistryRepositoryImageToImageRelProperties = (
        GCPArtifactRegistryRepositoryImageToImageRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label",
        set_in_kwargs=True,
    )
    _sub_resource_id: PropertyRef = PropertyRef(
        "_sub_resource_id",
        set_in_kwargs=True,
    )


@dataclass(frozen=True)
class GCPArtifactRegistryProjectToRepositoryImageRel(CartographyRelSchema):
    source_node_label: str = "GCPProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    target_node_label: str = "GCPArtifactRegistryRepositoryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryRepositoryImageMatchLinkProperties = (
        GCPArtifactRegistryRepositoryImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryToRepositoryImageRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryRepository"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    target_node_label: str = "GCPArtifactRegistryRepositoryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryRepositoryImageMatchLinkProperties = (
        GCPArtifactRegistryRepositoryImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryToRepositoryImageRepoImageRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryRepository"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    target_node_label: str = "GCPArtifactRegistryRepositoryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPO_IMAGE"
    properties: GCPArtifactRegistryRepositoryImageMatchLinkProperties = (
        GCPArtifactRegistryRepositoryImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToImageMatchLink(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryRepositoryImage"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("id")}
    )
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("digest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: GCPArtifactRegistryRepositoryImageMatchLinkProperties = (
        GCPArtifactRegistryRepositoryImageMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageSchema(CartographyNodeSchema):
    """A Google Cloud Artifact Registry Repository Image resource."""

    label: str = "GCPArtifactRegistryRepositoryImage"
    properties: GCPArtifactRegistryRepositoryImageNodeProperties = (
        GCPArtifactRegistryRepositoryImageNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryRepositoryImageToProjectRel = (
        GCPArtifactRegistryRepositoryImageToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryRepositoryImageToRepositoryRel(),
            GCPArtifactRegistryRepositoryImageToRepositoryRepoImageRel(),
            GCPArtifactRegistryRepositoryImageToImageRel(),
        ]
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ImageTag"])
