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
    id: PropertyRef = PropertyRef("containerArn")
    arn: PropertyRef = PropertyRef("containerArn", extra_index=True)
    task_arn: PropertyRef = PropertyRef("taskArn")
    name: PropertyRef = PropertyRef("name")
    image: PropertyRef = PropertyRef("image")
    image_digest: PropertyRef = PropertyRef("imageDigest")
    architecture: PropertyRef = PropertyRef("architecture")
    architecture_normalized: PropertyRef = PropertyRef("architecture_normalized")
    architecture_source: PropertyRef = PropertyRef("architecture_source")
    runtime_id: PropertyRef = PropertyRef("runtimeId")
    last_status: PropertyRef = PropertyRef("lastStatus", extra_index=True)
    exit_code: PropertyRef = PropertyRef("exitCode")
    reason: PropertyRef = PropertyRef("reason")
    health_status: PropertyRef = PropertyRef("healthStatus")
    cpu: PropertyRef = PropertyRef("cpu")
    memory: PropertyRef = PropertyRef("memory")
    memory_reservation: PropertyRef = PropertyRef("memoryReservation")
    gpu_ids: PropertyRef = PropertyRef("gpuIds")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "ECSTask"
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
# (:ECSContainer)-[:WORKLOAD_PARENT]->(:ECSTask)
class ECSContainerToECSTaskWorkloadParentRel(CartographyRelSchema):
    target_node_label: str = "ECSTask"
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
    target_node_label: str = "ECRImage"
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
    Relationship from ECSContainer to GitLabContainerImage.
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
class ECSContainerToGCPArtifactRegistryContainerImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToGCPArtifactRegistryContainerImageRel(CartographyRelSchema):
    """
    Matches containers to GAR image artifacts by runtime digest (imageDigest).
    """

    target_node_label: str = "GCPArtifactRegistryContainerImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("imageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ECSContainerToGCPArtifactRegistryContainerImageRelProperties = (
        ECSContainerToGCPArtifactRegistryContainerImageRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerToGCPArtifactRegistryPlatformImageRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerToGCPArtifactRegistryPlatformImageRel(CartographyRelSchema):
    """
    Matches containers to GAR platform manifests by runtime digest (imageDigest).
    """

    target_node_label: str = "GCPArtifactRegistryPlatformImage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"digest": PropertyRef("imageDigest")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_IMAGE"
    properties: ECSContainerToGCPArtifactRegistryPlatformImageRelProperties = (
        ECSContainerToGCPArtifactRegistryPlatformImageRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerSchema(CartographyNodeSchema):
    label: str = "ECSContainer"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Container"])
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
            ECSContainerToGCPArtifactRegistryContainerImageRel(),
            ECSContainerToGCPArtifactRegistryPlatformImageRel(),
        ]
    )
