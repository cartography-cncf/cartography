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
class ECSTaskNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("taskArn")
    arn: PropertyRef = PropertyRef("taskArn", extra_index=True)
    availability_zone: PropertyRef = PropertyRef("availabilityZone")
    capacity_provider_name: PropertyRef = PropertyRef("capacityProviderName")
    cluster_arn: PropertyRef = PropertyRef("clusterArn")
    connectivity: PropertyRef = PropertyRef("connectivity")
    connectivity_at: PropertyRef = PropertyRef("connectivityAt")
    container_instance_arn: PropertyRef = PropertyRef("containerInstanceArn")
    cpu: PropertyRef = PropertyRef("cpu")
    created_at: PropertyRef = PropertyRef("createdAt")
    desired_status: PropertyRef = PropertyRef("desiredStatus")
    enable_execute_command: PropertyRef = PropertyRef("enableExecuteCommand")
    execution_stopped_at: PropertyRef = PropertyRef("executionStoppedAt")
    group: PropertyRef = PropertyRef("group")
    service_name: PropertyRef = PropertyRef("serviceName")
    health_status: PropertyRef = PropertyRef("healthStatus")
    last_status: PropertyRef = PropertyRef("lastStatus")
    launch_type: PropertyRef = PropertyRef("launchType")
    memory: PropertyRef = PropertyRef("memory")
    platform_version: PropertyRef = PropertyRef("platformVersion")
    platform_family: PropertyRef = PropertyRef("platformFamily")
    pull_started_at: PropertyRef = PropertyRef("pullStartedAt")
    pull_stopped_at: PropertyRef = PropertyRef("pullStoppedAt")
    started_at: PropertyRef = PropertyRef("startedAt")
    started_by: PropertyRef = PropertyRef("startedBy")
    stop_code: PropertyRef = PropertyRef("stopCode")
    stopped_at: PropertyRef = PropertyRef("stoppedAt")
    stopped_reason: PropertyRef = PropertyRef("stoppedReason")
    stopping_at: PropertyRef = PropertyRef("stoppingAt")
    task_definition_arn: PropertyRef = PropertyRef("taskDefinitionArn")
    version: PropertyRef = PropertyRef("version")
    ephemeral_storage_size_in_gib: PropertyRef = PropertyRef(
        "ephemeralStorage.sizeInGiB"
    )
    network_interface_id: PropertyRef = PropertyRef("networkInterfaceId")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskToECSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskToECSClusterRel(CartographyRelSchema):
    target_node_label: str = "ECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TASK"
    properties: ECSTaskToECSClusterRelProperties = ECSTaskToECSClusterRelProperties()


@dataclass(frozen=True)
class ECSTaskToContainerInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskToContainerInstanceRel(CartographyRelSchema):
    target_node_label: str = "ECSContainerInstance"
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
    target_node_label: str = "NetworkInterface"
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
    label: str = "ECSTask"
    properties: ECSTaskNodeProperties = ECSTaskNodeProperties()
    sub_resource_relationship: ECSTaskToAWSAccountRel = ECSTaskToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSTaskToContainerInstanceRel(),
            ECSTaskToECSClusterRel(),
            ECSTaskToNetworkInterfaceRel(),
        ]
    )
