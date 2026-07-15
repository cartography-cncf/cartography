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
class ECSContainerInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "containerInstanceArn", description="The ARN of the container instance"
    )
    arn: PropertyRef = PropertyRef(
        "containerInstanceArn",
        extra_index=True,
        description="The ARN of the container instance",
    )
    ec2_instance_id: PropertyRef = PropertyRef(
        "ec2InstanceId",
        description="The ID of the container instance. For Amazon EC2 instances, this value is the Amazon EC2 instance ID. For external instances, this value is the AWS Systems Manager managed instance ID.",
    )
    capacity_provider_name: PropertyRef = PropertyRef(
        "capacityProviderName",
        description="The capacity provider that's associated with the container instance.",
    )
    version: PropertyRef = PropertyRef(
        "version", description="The version counter for the container instance."
    )
    version_info_agent_version: PropertyRef = PropertyRef(
        "versionInfo.agentVersion",
        description="The version number of the Amazon ECS container agent.",
    )
    version_info_agent_hash: PropertyRef = PropertyRef(
        "versionInfo.agentHash",
        description="The Git commit hash for the Amazon ECS container agent build on the amazon-ecs-agent  GitHub repository.",
    )
    version_info_agent_docker_version: PropertyRef = PropertyRef(
        "versionInfo.dockerVersion",
        description="The Docker version that's running on the container instance.",
    )
    status: PropertyRef = PropertyRef(
        "status", description="The status of the container instance."
    )
    status_reason: PropertyRef = PropertyRef(
        "statusReason",
        description="The reason that the container instance reached its current status.",
    )
    agent_connected: PropertyRef = PropertyRef(
        "agentConnected",
        description="This parameter returns true if the agent is connected to Amazon ECS. Registered instances with an agent that may be unhealthy or stopped return false.",
    )
    agent_update_status: PropertyRef = PropertyRef(
        "agentUpdateStatus",
        description="The status of the most recent agent update. If an update wasn't ever requested, this value is NULL.",
    )
    registered_at: PropertyRef = PropertyRef(
        "registeredAt",
        description="The Unix timestamp for the time when the container instance was registered.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the container instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSContainerInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerInstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSContainerInstance`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerInstanceToAWSAccountRelProperties = (
        ECSContainerInstanceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerInstanceToECSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerInstanceToECSClusterRel(CartographyRelSchema):
    "Represents a `HAS_CONTAINER_INSTANCE` relationship from `AWSECSCluster` to `AWSECSContainerInstance`."

    target_node_label: str = "AWSECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONTAINER_INSTANCE"
    properties: ECSContainerInstanceToECSClusterRelProperties = (
        ECSContainerInstanceToECSClusterRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerInstanceToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerInstanceToEC2InstanceRel(CartographyRelSchema):
    "Represents a `IS_INSTANCE` relationship from `AWSECSContainerInstance` to `AWSEC2Instance`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ec2InstanceId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_INSTANCE"
    properties: ECSContainerInstanceToEC2InstanceRelProperties = (
        ECSContainerInstanceToEC2InstanceRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerInstanceSchema(CartographyNodeSchema):
    "Represents an `AWSECSContainerInstance` node in the AWS graph."

    label: str = "AWSECSContainerInstance"
    # DEPRECATED: legacy ECSContainerInstance node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECSContainerInstance"])
    properties: ECSContainerInstanceNodeProperties = (
        ECSContainerInstanceNodeProperties()
    )
    sub_resource_relationship: ECSContainerInstanceToAWSAccountRel = (
        ECSContainerInstanceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSContainerInstanceToECSClusterRel(),
            ECSContainerInstanceToEC2InstanceRel(),
        ]
    )
