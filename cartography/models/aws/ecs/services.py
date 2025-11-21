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
class ECSServiceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("serviceArn")
    arn: PropertyRef = PropertyRef("serviceArn", extra_index=True)
    name: PropertyRef = PropertyRef("serviceName")
    cluster_arn: PropertyRef = PropertyRef("clusterArn")
    status: PropertyRef = PropertyRef("status")
    desired_count: PropertyRef = PropertyRef("desiredCount")
    running_count: PropertyRef = PropertyRef("runningCount")
    pending_count: PropertyRef = PropertyRef("pendingCount")
    launch_type: PropertyRef = PropertyRef("launchType")
    platform_version: PropertyRef = PropertyRef("platformVersion")
    platform_family: PropertyRef = PropertyRef("platformFamily")
    task_definition: PropertyRef = PropertyRef("taskDefinition")
    deployment_config_circuit_breaker_enable: PropertyRef = PropertyRef(
        "deploymentConfiguration.deploymentCircuitBreaker.enable"
    )
    deployment_config_circuit_breaker_rollback: PropertyRef = PropertyRef(
        "deploymentConfiguration.deploymentCircuitBreaker.rollback"
    )
    deployment_config_maximum_percent: PropertyRef = PropertyRef(
        "deploymentConfiguration.maximumPercent"
    )
    deployment_config_minimum_healthy_percent: PropertyRef = PropertyRef(
        "deploymentConfiguration.minimumHealthyPercent"
    )
    role_arn: PropertyRef = PropertyRef("roleArn")
    created_at: PropertyRef = PropertyRef("createdAt")
    health_check_grace_period_seconds: PropertyRef = PropertyRef(
        "healthCheckGracePeriodSeconds"
    )
    created_by: PropertyRef = PropertyRef("createdBy")
    enable_ecs_managed_tags: PropertyRef = PropertyRef("enableECSManagedTags")
    propagate_tags: PropertyRef = PropertyRef("propagateTags")
    enable_execute_command: PropertyRef = PropertyRef("enableExecuteCommand")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSServiceToECSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSServiceToECSClusterRel(CartographyRelSchema):
    target_node_label: str = "ECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_SERVICE"
    properties: ECSServiceToECSClusterRelProperties = (
        ECSServiceToECSClusterRelProperties()
    )


@dataclass(frozen=True)
class ECSServiceToTaskDefinitionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSServiceToTaskDefinitionRel(CartographyRelSchema):
    target_node_label: str = "ECSTaskDefinition"
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


@dataclass(frozen=True)
class ECSServiceToECSTaskRel(CartographyRelSchema):
    target_node_label: str = "ECSTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"service_name": PropertyRef("serviceName")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TASK"
    properties: ECSServiceToECSTaskRelProperties = ECSServiceToECSTaskRelProperties()


@dataclass(frozen=True)
class ECSServiceSchema(CartographyNodeSchema):
    label: str = "ECSService"
    properties: ECSServiceNodeProperties = ECSServiceNodeProperties()
    sub_resource_relationship: ECSServiceToAWSAccountRel = ECSServiceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSServiceToECSClusterRel(),
            ECSServiceToTaskDefinitionRel(),
            ECSServiceToECSTaskRel(),
        ]
    )
