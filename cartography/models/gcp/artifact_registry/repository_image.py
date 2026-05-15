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
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    uri: PropertyRef = PropertyRef("uri", extra_index=True)
    _ont_uri: PropertyRef = PropertyRef("uri")
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    tag: PropertyRef = PropertyRef("tag")
    _ont_tag: PropertyRef = PropertyRef("tag")
    tags: PropertyRef = PropertyRef("tags")
    resource_name: PropertyRef = PropertyRef("resource_name", extra_index=True)
    digest_uri: PropertyRef = PropertyRef("digest_uri")
    image_size_bytes: PropertyRef = PropertyRef("image_size_bytes")
    media_type: PropertyRef = PropertyRef("media_type")
    upload_time: PropertyRef = PropertyRef("upload_time")
    build_time: PropertyRef = PropertyRef("build_time")
    update_time: PropertyRef = PropertyRef("update_time")
    artifact_type: PropertyRef = PropertyRef("artifact_type")
    repository_id: PropertyRef = PropertyRef("repository_id")
    project_id: PropertyRef = PropertyRef("project_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryImageToProjectRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


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
