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
class ECRRepositoryImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    tag: PropertyRef = PropertyRef("imageTag")
    uri: PropertyRef = PropertyRef("uri")
    repo_uri: PropertyRef = PropertyRef("repo_uri")
    image_size_bytes: PropertyRef = PropertyRef("imageSizeInBytes")
    image_pushed_at: PropertyRef = PropertyRef("imagePushedAt")
    image_manifest_media_type: PropertyRef = PropertyRef("imageManifestMediaType")
    artifact_media_type: PropertyRef = PropertyRef("artifactMediaType")
    last_recorded_pull_time: PropertyRef = PropertyRef("lastRecordedPullTime")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryImageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryImageToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECRRepositoryImageToAWSAccountRelProperties = (
        ECRRepositoryImageToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECRRepositoryImageToECRRepositoryRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryImageToECRRepositoryRel(CartographyRelSchema):
    target_node_label: str = "ECRRepository"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"uri": PropertyRef("repo_uri")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "REPO_IMAGE"
    properties: ECRRepositoryImageToECRRepositoryRelProperties = (
        ECRRepositoryImageToECRRepositoryRelProperties()
    )


@dataclass(frozen=True)
class ECRRepositoryImageToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryImageToECRImageRel(CartographyRelSchema):
    target_node_label: str = "ECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("imageDigests", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IMAGE"
    properties: ECRRepositoryImageToECRImageRelProperties = (
        ECRRepositoryImageToECRImageRelProperties()
    )


@dataclass(frozen=True)
class ECRRepositoryImageSchema(CartographyNodeSchema):
    label: str = "ECRRepositoryImage"
    properties: ECRRepositoryImageNodeProperties = ECRRepositoryImageNodeProperties()
    sub_resource_relationship: ECRRepositoryImageToAWSAccountRel = (
        ECRRepositoryImageToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECRRepositoryImageToECRRepositoryRel(),
            ECRRepositoryImageToECRImageRel(),
        ]
    )
