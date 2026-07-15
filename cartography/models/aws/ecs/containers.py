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
class ECSContainerNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "containerArn", description="The ARN of the container"
    )
    arn: PropertyRef = PropertyRef(
        "containerArn", extra_index=True, description="The arn of the container."
    )
    task_arn: PropertyRef = PropertyRef("taskArn", description="The ARN of the task.")
    name: PropertyRef = PropertyRef("name", description="The name of the container.")
    image: PropertyRef = PropertyRef(
        "image", description="The image used for the container."
    )
    image_digest: PropertyRef = PropertyRef(
        "imageDigest", description="The container image manifest digest."
    )
    architecture: PropertyRef = PropertyRef(
        "architecture",
        description="Raw container architecture value captured from ECS runtime/task definition (for example, `x86_64`, `ARM64`).",
    )
    architecture_normalized: PropertyRef = PropertyRef(
        "architecture_normalized",
        description="Canonicalized architecture value (for example, `amd64`, `arm64`, `arm`, `386`, `unknown`).",
    )
    architecture_source: PropertyRef = PropertyRef(
        "architecture_source",
        description="Source for architecture inference (`runtime_api_exact` or `task_definition_hint`).",
    )
    runtime_id: PropertyRef = PropertyRef(
        "runtimeId", description="The ID of the Docker container."
    )
    last_status: PropertyRef = PropertyRef(
        "lastStatus",
        extra_index=True,
        description="The last known status of the container.",
    )
    exit_code: PropertyRef = PropertyRef(
        "exitCode", description="The exit code returned from the container."
    )
    reason: PropertyRef = PropertyRef(
        "reason",
        description="A short (255 max characters) human-readable string to provide additional details about a running or stopped container.",
    )
    health_status: PropertyRef = PropertyRef(
        "healthStatus", description="The health status of the container."
    )
    cpu: PropertyRef = PropertyRef(
        "cpu", description="The number of CPU units set for the container."
    )
    memory: PropertyRef = PropertyRef(
        "memory", description="The hard limit (in MiB) of memory set for the container."
    )
    memory_reservation: PropertyRef = PropertyRef(
        "memoryReservation",
        description="The soft limit (in MiB) of memory set for the container.",
    )
    gpu_ids: PropertyRef = PropertyRef(
        "gpuIds", description="The IDs of each GPU assigned to the container."
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the container."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSContainerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSContainer`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerToAWSAccountRelProperties = (
        ECSContainerToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerToTaskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class ECSContainerToTaskRel(CartographyRelSchema):
    "Represents a `HAS_CONTAINER` relationship from `AWSECSTask` to `AWSECSContainer`."

    target_node_label: str = "AWSECSTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("taskArn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONTAINER"
    properties: ECSContainerToTaskRelProperties = ECSContainerToTaskRelProperties()


@dataclass(frozen=True)
class ECSContainerToECSTaskWorkloadParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSECSContainer)-[:WORKLOAD_PARENT]->(:AWSECSTask)
class ECSContainerToECSTaskWorkloadParentRel(CartographyRelSchema):
    "Represents a `WORKLOAD_PARENT` relationship from `AWSECSContainer` to `AWSECSTask`."

    target_node_label: str = "AWSECSTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("taskArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ECSContainerToECSTaskWorkloadParentRelProperties = (
        ECSContainerToECSTaskWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerToECRImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToECRImageRel(CartographyRelSchema):
    "Represents a `HAS_IMAGE` relationship from `AWSECSContainer` to `AWSECRImage`."

    target_node_label: str = "AWSECRImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("imageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ECSContainerToECRImageRelProperties = (
        ECSContainerToECRImageRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerToGitLabContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToGitLabContainerImageRel(CartographyRelSchema):
    """
    Relationship from AWSECSContainer to GitLabContainerImage.
    Matches containers to GitLab registry images by runtime digest (imageDigest).
    """

    target_node_label: str = "GitLabContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("imageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ECSContainerToGitLabContainerImageRelProperties = (
        ECSContainerToGitLabContainerImageRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerToGCPArtifactRegistryImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToGCPArtifactRegistryImageRel(CartographyRelSchema):
    """
    Matches containers to GAR image artifacts by runtime digest (imageDigest).
    """

    target_node_label: str = "GCPArtifactRegistryImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("imageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ECSContainerToGCPArtifactRegistryImageRelProperties = (
        ECSContainerToGCPArtifactRegistryImageRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerToGitHubContainerImageRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToGitHubContainerImageRel(CartographyRelSchema):
    """
    Matches containers to GitHub Container Registry images by runtime digest (imageDigest).
    """

    target_node_label: str = "GitHubContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("imageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ECSContainerToGitHubContainerImageRelProperties = (
        ECSContainerToGitHubContainerImageRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerSchema(CartographyNodeSchema):
    "Represents an `AWSECSContainer` node in the AWS graph."

    label: str = "AWSECSContainer"
    # DEPRECATED: legacy ECSContainer node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECSContainer", "Container"])
    properties: ECSContainerNodeProperties = ECSContainerNodeProperties()
    sub_resource_relationship: ECSContainerToAWSAccountRel = (
        ECSContainerToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSContainerToTaskRel(),
            ECSContainerToECSTaskWorkloadParentRel(),
            ECSContainerToECRImageRel(),
            ECSContainerToGitLabContainerImageRel(),
            ECSContainerToGCPArtifactRegistryImageRel(),
            ECSContainerToGitHubContainerImageRel(),
        ]
    )
