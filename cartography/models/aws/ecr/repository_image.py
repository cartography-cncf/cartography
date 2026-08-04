from dataclasses import dataclass

from cartography.models.aws.extra_labels import LEGACY_ECR_REPOSITORY_IMAGE
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
from cartography.models.ontology.labels import IMAGE_TAG


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
    """An ECR image may be referenced and tagged by more than one ECR Repository. To best represent this, we've created an `AWSECRRepositoryImage` node as a layer of indirection between the repo and the image.

    More concretely explained, we run [`ecr.list_images()`](https://docs.aws.amazon.com/AmazonECR/latest/APIReference/API_ImageIdentifier.html), and then store the image tag on an `AWSECRRepositoryImage` node and the image digest hash on a separate `AWSECRImage` node.

    This way, more than one `AWSECRRepositoryImage` can reference/be connected to the same `AWSECRImage`.
    """

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
        [LEGACY_ECR_REPOSITORY_IMAGE, IMAGE_TAG]
    )
