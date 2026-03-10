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
class DockerScoutPublicImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    name: PropertyRef = PropertyRef("name")
    tag: PropertyRef = PropertyRef("tag")
    version: PropertyRef = PropertyRef("version")
    digest: PropertyRef = PropertyRef("digest")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageToImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class DockerScoutPublicImageToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutPublicImageToImageRelProperties = (
        DockerScoutPublicImageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageToGCPImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutPublicImageToImageRelProperties = (
        DockerScoutPublicImageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageToGCPPlatformImageRel(CartographyRelSchema):
    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutPublicImageToImageRelProperties = (
        DockerScoutPublicImageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageToGitLabImageRel(CartographyRelSchema):
    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ImageDigest")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BUILT_ON"
    properties: DockerScoutPublicImageToImageRelProperties = (
        DockerScoutPublicImageToImageRelProperties()
    )


@dataclass(frozen=True)
class DockerScoutPublicImageSchema(CartographyNodeSchema):
    label: str = "DockerScoutPublicImage"
    scoped_cleanup: bool = False
    properties: DockerScoutPublicImageNodeProperties = (
        DockerScoutPublicImageNodeProperties()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            DockerScoutPublicImageToECRImageRel(),
            DockerScoutPublicImageToGCPImageRel(),
            DockerScoutPublicImageToGCPPlatformImageRel(),
            DockerScoutPublicImageToGitLabImageRel(),
        ],
    )
