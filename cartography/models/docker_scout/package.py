from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class DockerScoutPackageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    version: PropertyRef = PropertyRef("version")
    namespace: PropertyRef = PropertyRef("namespace")
    type: PropertyRef = PropertyRef("type")
    purl: PropertyRef = PropertyRef("purl")
    normalized_id: PropertyRef = PropertyRef(
        "normalized_id", extra_index=True
    )  # Format: {type}|{namespace/}{normalized_name}|{version}
    layer_digest: PropertyRef = PropertyRef("layer_digest")
    layer_diff_id: PropertyRef = PropertyRef("layer_diff_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPackageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPackageToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: DockerScoutPackageToImageRelProperties = (
        DockerScoutPackageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPackageToGCPImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: DockerScoutPackageToImageRelProperties = (
        DockerScoutPackageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPackageToGCPPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: DockerScoutPackageToImageRelProperties = (
        DockerScoutPackageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPackageToGitLabImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "DEPLOYED"
    properties: DockerScoutPackageToImageRelProperties = (
        DockerScoutPackageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPackageToBaseImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPackageToBaseImageRel(CartographyRelSchema):
    target_node_label: str = "DockerScoutPublicImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("BaseImageId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "FROM_BASE"
    properties: DockerScoutPackageToBaseImageRelProperties = (
        DockerScoutPackageToBaseImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPackageSchema(CartographyNodeSchema):
    label: str = "DockerScoutPackage"
    scoped_cleanup: bool = False
    properties: DockerScoutPackageNodeProperties = DockerScoutPackageNodeProperties()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutPackageToECRImageRel(),
            DockerScoutPackageToGCPImageRel(),
            DockerScoutPackageToGCPPlatformImageRel(),
            DockerScoutPackageToGitLabImageRel(),
            DockerScoutPackageToBaseImageRel(),
        ],
    )
