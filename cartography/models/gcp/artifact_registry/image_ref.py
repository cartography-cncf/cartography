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
class GCPArtifactRegistryImageRefNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", extra_index=True)
    name: PropertyRef = PropertyRef("name")
    uri: PropertyRef = PropertyRef("uri", extra_index=True)
    digest: PropertyRef = PropertyRef("digest", extra_index=True)
    tags: PropertyRef = PropertyRef("tags")
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
class GCPArtifactRegistryImageRefToProjectRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToProjectRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryImageRefToProjectRelProperties = (
        GCPArtifactRegistryImageRefToProjectRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToRepositoryRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryImageRefToRepositoryRelProperties = (
        GCPArtifactRegistryImageRefToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToRepositoryRepoImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPO_IMAGE"
    properties: GCPArtifactRegistryImageRefToRepositoryRelProperties = (
        GCPArtifactRegistryImageRefToRepositoryRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("digest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: GCPArtifactRegistryImageRefToImageRelProperties = (
        GCPArtifactRegistryImageRefToImageRelProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefMatchLinkProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    _sub_resource_label: PropertyRef = PropertyRef(
        "_sub_resource_label", set_in_kwargs=True
    )
    _sub_resource_id: PropertyRef = PropertyRef("_sub_resource_id", set_in_kwargs=True)


@dataclass(frozen=True)
class GCPArtifactRegistryProjectToImageRefRel(CartographyRelSchema):
    source_node_label: str = "GCPProject"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)}
    )
    target_node_label: str = "GCPArtifactRegistryImageRef"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: GCPArtifactRegistryImageRefMatchLinkProperties = (
        GCPArtifactRegistryImageRefMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryToImageRefRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryRepository"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    target_node_label: str = "GCPArtifactRegistryImageRef"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONTAINS"
    properties: GCPArtifactRegistryImageRefMatchLinkProperties = (
        GCPArtifactRegistryImageRefMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryRepositoryToImageRefRepoImageRel(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryRepository"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("repository_id")}
    )
    target_node_label: str = "GCPArtifactRegistryImageRef"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("id")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "REPO_IMAGE"
    properties: GCPArtifactRegistryImageRefMatchLinkProperties = (
        GCPArtifactRegistryImageRefMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefToImageMatchLink(CartographyRelSchema):
    source_node_label: str = "GCPArtifactRegistryImageRef"
    source_node_matcher: SourceNodeMatcher = make_source_node_matcher(
        {"id": PropertyRef("id")}
    )
    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("digest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: GCPArtifactRegistryImageRefMatchLinkProperties = (
        GCPArtifactRegistryImageRefMatchLinkProperties()
    )


@dataclass(frozen=True)
class GCPArtifactRegistryImageRefSchema(CartographyNodeSchema):
    label: str = "GCPArtifactRegistryImageRef"
    properties: GCPArtifactRegistryImageRefNodeProperties = (
        GCPArtifactRegistryImageRefNodeProperties()
    )
    sub_resource_relationship: GCPArtifactRegistryImageRefToProjectRel = (
        GCPArtifactRegistryImageRefToProjectRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            GCPArtifactRegistryImageRefToRepositoryRel(),
            GCPArtifactRegistryImageRefToRepositoryRepoImageRel(),
            GCPArtifactRegistryImageRefToImageRel(),
        ]
    )
    # DEPRECATED: GCPArtifactRegistryContainerImage compatibility label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ImageTag", "GCPArtifactRegistryContainerImage"]
    )
