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
class ECSServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("serviceArn", description="The ARN of the service")
    arn: PropertyRef = PropertyRef(
        "serviceArn", extra_index=True, description="The ARN of the service"
    )
    name: PropertyRef = PropertyRef(
        "serviceName", description="The name of your service."
    )
    cluster_arn: PropertyRef = PropertyRef(
        "clusterArn",
        description="The Amazon Resource Name (ARN) of the cluster that hosts the service.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="The status of the service."
    )
    desired_count: PropertyRef = PropertyRef(
        "desiredCount",
        description="The desired number of instantiations of the task definition to keep running on the service.",
    )
    running_count: PropertyRef = PropertyRef(
        "runningCount",
        description="The number of tasks in the cluster that are in the RUNNING state.",
    )
    pending_count: PropertyRef = PropertyRef(
        "pendingCount",
        description="The number of tasks in the cluster that are in the PENDING state.",
    )
    launch_type: PropertyRef = PropertyRef(
        "launchType", description="The launch type the service is using."
    )
    platform_version: PropertyRef = PropertyRef(
        "platformVersion",
        description="The platform version to run your service on. A platform version is only specified for tasks that are hosted on AWS Fargate.",
    )
    platform_family: PropertyRef = PropertyRef(
        "platformFamily",
        description="The operating system that your tasks in the service run on. A platform family is specified only for tasks using the Fargate launch type.",
    )
    task_definition: PropertyRef = PropertyRef(
        "taskDefinition",
        description="The task definition to use for tasks in the service.",
    )
    deployment_config_circuit_breaker_enable: PropertyRef = PropertyRef(
        "deploymentConfiguration.deploymentCircuitBreaker.enable",
        description="Determines whether to enable the deployment circuit breaker logic for the service.",
    )
    deployment_config_circuit_breaker_rollback: PropertyRef = PropertyRef(
        "deploymentConfiguration.deploymentCircuitBreaker.rollback",
        description="Determines whether to enable Amazon ECS to roll back the service if a service deployment fails.",
    )
    deployment_config_maximum_percent: PropertyRef = PropertyRef(
        "deploymentConfiguration.maximumPercent",
        description="If a service is using the rolling update (ECS) deployment type, the maximum percent parameter represents an upper limit on the number of tasks in a service that are allowed in the RUNNING or PENDING state during a deployment, as a percentage of the desired number of tasks (rounded down to the nearest integer), and while any container instances are in the DRAINING state if the service contains tasks using the EC2 launch type.",
    )
    deployment_config_minimum_healthy_percent: PropertyRef = PropertyRef(
        "deploymentConfiguration.minimumHealthyPercent",
        description="If a service is using the rolling update (ECS) deployment type, the minimum healthy percent represents a lower limit on the number of tasks in a service that must remain in the RUNNING state during a deployment, as a percentage of the desired number of tasks (rounded up to the nearest integer), and while any container instances are in the DRAINING state if the service contains tasks using the EC2 launch type.",
    )
    role_arn: PropertyRef = PropertyRef(
        "roleArn",
        description="The ARN of the IAM role that's associated with the service.",
    )
    created_at: PropertyRef = PropertyRef(
        "createdAt",
        description="The Unix timestamp for the time when the service was created.",
    )
    health_check_grace_period_seconds: PropertyRef = PropertyRef(
        "healthCheckGracePeriodSeconds",
        description="The period of time, in seconds, that the Amazon ECS service scheduler ignores unhealthy Elastic Load Balancing target health checks after a task has first started.",
    )
    created_by: PropertyRef = PropertyRef(
        "createdBy", description="The principal that created the service."
    )
    enable_ecs_managed_tags: PropertyRef = PropertyRef(
        "enableECSManagedTags",
        description="Determines whether to enable Amazon ECS managed tags for the tasks in the service.",
    )
    propagate_tags: PropertyRef = PropertyRef(
        "propagateTags",
        description="Determines whether to propagate the tags from the task definition or the service to the task.",
    )
    enable_execute_command: PropertyRef = PropertyRef(
        "enableExecuteCommand",
        description="Determines whether the execute command functionality is enabled for the service.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the service."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSServiceToECSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class ECSServiceToECSClusterRel(CartographyRelSchema):
    "Represents a `HAS_SERVICE` relationship from `AWSECSCluster` to `AWSECSService`."

    target_node_label: str = "AWSECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SERVICE"
    properties: ECSServiceToECSClusterRelProperties = (
        ECSServiceToECSClusterRelProperties()
    )


@dataclass(frozen=True)
class ECSServiceToECSClusterWorkloadParentRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSECSService)-[:WORKLOAD_PARENT]->(:AWSECSCluster)
class ECSServiceToECSClusterWorkloadParentRel(CartographyRelSchema):
    "Represents a `WORKLOAD_PARENT` relationship from `AWSECSService` to `AWSECSCluster`."

    target_node_label: str = "AWSECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "WORKLOAD_PARENT"
    properties: ECSServiceToECSClusterWorkloadParentRelProperties = (
        ECSServiceToECSClusterWorkloadParentRelProperties()
    )


@dataclass(frozen=True)
class ECSServiceToTaskDefinitionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSServiceToTaskDefinitionRel(CartographyRelSchema):
    "Represents a `HAS_TASK_DEFINITION` relationship from `AWSECSService` to `AWSECSTaskDefinition`."

    target_node_label: str = "AWSECSTaskDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("taskDefinition")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TASK_DEFINITION"
    properties: ECSServiceToTaskDefinitionRelProperties = (
        ECSServiceToTaskDefinitionRelProperties()
    )


@dataclass(frozen=True)
class ECSServiceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSServiceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSService`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSServiceToAWSAccountRelProperties = (
        ECSServiceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECSServiceToECSTaskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# DEPRECATED: replaced by WORKLOAD_PARENT, will be removed in v1.0.0
@dataclass(frozen=True)
class ECSServiceToECSTaskRel(CartographyRelSchema):
    "Represents a `HAS_TASK` relationship from `AWSECSService` to `AWSECSTask`."

    target_node_label: str = "AWSECSTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "service_name": PropertyRef("serviceName"),
            "cluster_arn": PropertyRef("clusterArn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TASK"
    properties: ECSServiceToECSTaskRelProperties = ECSServiceToECSTaskRelProperties()


@dataclass(frozen=True)
class ECSServiceSchema(CartographyNodeSchema):
    "Represents an `AWSECSService` node in the AWS graph."

    label: str = "AWSECSService"
    # DEPRECATED: legacy ECSService node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(
        ["ECSService", "ComputeService"]
    )
    properties: ECSServiceNodeProperties = ECSServiceNodeProperties()
    sub_resource_relationship: ECSServiceToAWSAccountRel = ECSServiceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSServiceToECSClusterRel(),
            ECSServiceToECSClusterWorkloadParentRel(),
            ECSServiceToTaskDefinitionRel(),
            ECSServiceToECSTaskRel(),
        ]
    )
