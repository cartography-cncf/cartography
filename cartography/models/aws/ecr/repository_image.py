from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ECRRepositoryImageNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="same as uri")
    tag: PropertyRef = PropertyRef(
        "imageTag", description='The tag applied to the repository image, e.g. "latest"'
    )
    uri: PropertyRef = PropertyRef(
        "uri", description="The URI where the repository image is stored"
    )
    repo_uri: PropertyRef = PropertyRef(
        "repo_uri",
        description="URI of the ECR repository containing the image.",
    )
    image_size_bytes: PropertyRef = PropertyRef(
        "imageSizeInBytes", description="The size of the image in bytes"
    )
    image_pushed_at: PropertyRef = PropertyRef(
        "imagePushedAt",
        description="The date and time the image was pushed to the repository",
    )
    image_manifest_media_type: PropertyRef = PropertyRef(
        "imageManifestMediaType",
        description="The media type of the image manifest, see [opencontainers image spec](https://github.com/opencontainers/image-spec/blob/main/media-types.md)",
    )
    artifact_media_type: PropertyRef = PropertyRef(
        "artifactMediaType", description="The media type of the image artifact"
    )
    last_recorded_pull_time: PropertyRef = PropertyRef(
        "lastRecordedPullTime",
        description="The date and time the image was last pulled",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSECRRepositoryImage` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSECRRepositoryImage` node.",
    )


@dataclass(frozen=True)
class ECRRepositoryImageToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECRRepositoryImageToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECRRepositoryImage`."

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
    "Represents a `REPO_IMAGE` relationship from `AWSECRRepository` to `AWSECRRepositoryImage`."

    target_node_label: str = "AWSECRRepository"
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
    "Represents a `IMAGE` relationship from `AWSECRRepositoryImage` to `AWSECRImage`."

    target_node_label: str = "AWSECRImage"
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
    "Represents an `AWSECRRepositoryImage` node in the AWS graph."

    label: str = "AWSECRRepositoryImage"
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
    # DEPRECATED: legacy ECRRepositoryImage node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ECRRepositoryImage", "ImageTag"]
    )
