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
class ECSTaskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("taskArn", description="The ARN of the task")
    arn: PropertyRef = PropertyRef(
        "taskArn", extra_index=True, description="The arn of the task."
    )
    availability_zone: PropertyRef = PropertyRef(
        "availabilityZone", description="The Availability Zone for the task."
    )
    capacity_provider_name: PropertyRef = PropertyRef(
        "capacityProviderName",
        description="The capacity provider that's associated with the task.",
    )
    cluster_arn: PropertyRef = PropertyRef(
        "clusterArn", description="The ARN of the cluster that hosts the task."
    )
    connectivity: PropertyRef = PropertyRef(
        "connectivity", description="The connectivity status of a task."
    )
    connectivity_at: PropertyRef = PropertyRef(
        "connectivityAt",
        description="The Unix timestamp for the time when the task last went into CONNECTED status.",
    )
    container_instance_arn: PropertyRef = PropertyRef(
        "containerInstanceArn",
        description="The ARN of the container instances that host the task.",
    )
    cpu: PropertyRef = PropertyRef(
        "cpu",
        description="The number of CPU units used by the task as expressed in a task definition.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt",
        description="The Unix timestamp for the time when the task was created. More specifically, it's for the time when the task entered the PENDING state.",
    )
    desired_status: PropertyRef = PropertyRef(
        "desiredStatus", description="The desired status of the task."
    )
    enable_execute_command: PropertyRef = PropertyRef(
        "enableExecuteCommand",
        extra_index=True,
        description="Determines whether execute command functionality is enabled for this task.",
    )
    execution_stopped_at: PropertyRef = PropertyRef(
        "executionStoppedAt",
        description="The Unix timestamp for the time when the task execution stopped.",
    )
    group: PropertyRef = PropertyRef(
        "group",
        description="The name of the task group that's associated with the task.",
    )
    service_name: PropertyRef = PropertyRef(
        "serviceName",
        description="Name of the ECS service that launched the task.",
    )
    health_status: PropertyRef = PropertyRef(
        "healthStatus", description="The health status for the task."
    )
    last_status: PropertyRef = PropertyRef(
        "lastStatus", description="The last known status for the task."
    )
    launch_type: PropertyRef = PropertyRef(
        "launchType", description="The infrastructure where your task runs on."
    )
    memory: PropertyRef = PropertyRef(
        "memory",
        description="The amount of memory (in MiB) that the task uses as expressed in a task definition.",
    )
    platform_version: PropertyRef = PropertyRef(
        "platformVersion", description="The platform version where your task runs on."
    )
    platform_family: PropertyRef = PropertyRef(
        "platformFamily",
        description="The operating system that your tasks are running on.",
    )
    pull_started_at: PropertyRef = PropertyRef(
        "pullStartedAt",
        description="The Unix timestamp for the time when the container image pull began.",
    )
    pull_stopped_at: PropertyRef = PropertyRef(
        "pullStoppedAt",
        description="The Unix timestamp for the time when the container image pull completed.",
    )
    started_at: PropertyRef = PropertyRef(
        "startedAt",
        description="The Unix timestamp for the time when the task started. More specifically, it's for the time when the task transitioned from the PENDING state to the RUNNING state.",
    )
    started_by: PropertyRef = PropertyRef(
        "startedBy",
        description="The tag specified when a task is started. If an Amazon ECS service started the task, the startedBy parameter contains the deployment ID of that service.",
    )
    stop_code: PropertyRef = PropertyRef(
        "stopCode", description="The stop code indicating why a task was stopped."
    )
    stopped_at: PropertyRef = PropertyRef(
        "stoppedAt",
        description="The Unix timestamp for the time when the task was stopped. More specifically, it's for the time when the task transitioned from the RUNNING state to the STOPPED state.",
    )
    stopped_reason: PropertyRef = PropertyRef(
        "stoppedReason", description="The reason that the task was stopped."
    )
    stopping_at: PropertyRef = PropertyRef(
        "stoppingAt",
        description="The Unix timestamp for the time when the task stops. More specifically, it's for the time when the task transitions from the RUNNING state to STOPPED.",
    )
    task_definition_arn: PropertyRef = PropertyRef(
        "taskDefinitionArn",
        description="The ARN of the task definition that creates the task.",
    )
    version: PropertyRef = PropertyRef(
        "version", description="The version counter for the task."
    )
    ephemeral_storage_size_in_gib: PropertyRef = PropertyRef(
        "ephemeralStorage.sizeInGiB",
        description="The total amount, in GiB, of ephemeral storage to set for the task.",
    )
    network_interface_id: PropertyRef = PropertyRef(
        "networkInterfaceId",
        description="The network interface ID for tasks running in awsvpc network mode.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the task."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSTaskToECSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class ECSTaskToECSClusterRel(CartographyRelSchema):
    "Represents a `HAS_TASK` relationship from `AWSECSCluster` to `AWSECSTask`."

    target_node_label: str = "AWSECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TASK"
    properties: ECSTaskToECSClusterRelProperties = ECSTaskToECSClusterRelProperties()


@dataclass(frozen=True)
class ECSTaskToECSServiceWorkloadParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSECSTask)-[:WORKLOAD_PARENT]->(:AWSECSService)
# Only fires when the task is associated with a service (serviceName extracted
# from the task's `group` field by the loader). Standalone tasks fall through
# to ECSTaskToECSClusterWorkloadParentRel.
class ECSTaskToECSServiceWorkloadParentRel(CartographyRelSchema):
    "Represents a `WORKLOAD_PARENT` relationship from `AWSECSTask` to `AWSECSService`."

    target_node_label: str = "AWSECSService"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "name": PropertyRef("serviceName"),
            "cluster_arn": PropertyRef("clusterArn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ECSTaskToECSServiceWorkloadParentRelProperties = (
        ECSTaskToECSServiceWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskToECSClusterWorkloadParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSECSTask)-[:WORKLOAD_PARENT]->(:AWSECSCluster)
# Fallback parent for standalone tasks (no service). The matcher is gated on
# `_workload_parent_cluster_arn`, which the ECS loader sets only when the task
# has no serviceName, so service-attached tasks don't get a duplicate edge.
class ECSTaskToECSClusterWorkloadParentRel(CartographyRelSchema):
    "Represents a `WORKLOAD_PARENT` relationship from `AWSECSTask` to `AWSECSCluster`."

    target_node_label: str = "AWSECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_workload_parent_cluster_arn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ECSTaskToECSClusterWorkloadParentRelProperties = (
        ECSTaskToECSClusterWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskToContainerInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskToContainerInstanceRel(CartographyRelSchema):
    "Represents a `HAS_TASK` relationship from `AWSECSContainerInstance` to `AWSECSTask`."

    target_node_label: str = "AWSECSContainerInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("containerInstanceArn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TASK"
    properties: ECSTaskToContainerInstanceRelProperties = (
        ECSTaskToContainerInstanceRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSTask`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSTaskToAWSAccountRelProperties = ECSTaskToAWSAccountRelProperties()


@dataclass(frozen=True)
class ECSTaskToNetworkInterfaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskToNetworkInterfaceRel(CartographyRelSchema):
    "Represents a `NETWORK_INTERFACE` relationship from `AWSECSTask` to `AWSNetworkInterface`."

    target_node_label: str = "AWSNetworkInterface"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("networkInterfaceId")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NETWORK_INTERFACE"
    properties: ECSTaskToNetworkInterfaceRelProperties = (
        ECSTaskToNetworkInterfaceRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskSchema(CartographyNodeSchema):
    "Represents an `AWSECSTask` node in the AWS graph."

    label: str = "AWSECSTask"
    # DEPRECATED: legacy ECSTask node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECSTask", "ComputePod"])
    properties: ECSTaskNodeProperties = ECSTaskNodeProperties()
    sub_resource_relationship: ECSTaskToAWSAccountRel = ECSTaskToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSTaskToContainerInstanceRel(),
            ECSTaskToECSClusterRel(),
            ECSTaskToECSServiceWorkloadParentRel(),
            ECSTaskToECSClusterWorkloadParentRel(),
            ECSTaskToNetworkInterfaceRel(),
        ]
    )
