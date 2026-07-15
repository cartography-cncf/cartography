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
class ECSTaskDefinitionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "taskDefinitionArn", description="The ARN of the task definition"
    )
    arn: PropertyRef = PropertyRef(
        "taskDefinitionArn",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSECSTaskDefinition` node.",
    )
    family: PropertyRef = PropertyRef(
        "family",
        description="The name of a family that this task definition is registered to.",
    )
    task_role_arn: PropertyRef = PropertyRef(
        "taskRoleArn",
        description="The short name or full Amazon Resource Name (ARN) of the AWS Identity and Access Management role that grants containers in the task permission to call AWS APIs on your behalf.",
    )
    execution_role_arn: PropertyRef = PropertyRef(
        "executionRoleArn",
        description="The Amazon Resource Name (ARN) of the task execution role that grants the Amazon ECS container agent permission to make AWS API calls on your behalf.",
    )
    network_mode: PropertyRef = PropertyRef(
        "networkMode",
        description="The Docker networking mode to use for the containers in the task. The valid values are none, bridge, awsvpc, and host. If no network mode is specified, the default is bridge.",
    )
    revision: PropertyRef = PropertyRef(
        "revision", description="The revision of the task in a particular family."
    )
    status: PropertyRef = PropertyRef(
        "status", description="The status of the task definition."
    )
    compatibilities: PropertyRef = PropertyRef(
        "compatibilities",
        description="The task launch types the task definition validated against during task definition registration.",
    )
    runtime_platform_cpu_architecture: PropertyRef = PropertyRef(
        "runtimePlatform.cpuArchitecture",
        description="The CPU architecture.",
    )
    runtime_platform_operating_system_family: PropertyRef = PropertyRef(
        "runtimePlatform.operatingSystemFamily",
        description="The operating system.",
    )
    requires_compatibilities: PropertyRef = PropertyRef(
        "requiresCompatibilities",
        description="The task launch types the task definition was validated against.",
    )
    cpu: PropertyRef = PropertyRef(
        "cpu", description="The number of cpu units used by the task."
    )
    memory: PropertyRef = PropertyRef(
        "memory", description="The amount (in MiB) of memory used by the task."
    )
    pid_mode: PropertyRef = PropertyRef(
        "pidMode",
        description="The process namespace to use for the containers in the task.",
    )
    ipc_mode: PropertyRef = PropertyRef(
        "ipcMode",
        description="The IPC resource namespace to use for the containers in the task.",
    )
    proxy_configuration_type: PropertyRef = PropertyRef(
        "proxyConfiguration.type", description="The proxy type."
    )
    proxy_configuration_container_name: PropertyRef = PropertyRef(
        "proxyConfiguration.containerName",
        description="The name of the container that will serve as the App Mesh proxy.",
    )
    registered_at: PropertyRef = PropertyRef(
        "registeredAt",
        description="The Unix timestamp for the time when the task definition was registered.",
    )
    deregistered_at: PropertyRef = PropertyRef(
        "deregisteredAt",
        description="The Unix timestamp for the time when the task definition was deregistered.",
    )
    registered_by: PropertyRef = PropertyRef(
        "registeredBy", description="The principal that registered the task definition."
    )
    ephemeral_storage_size_in_gib: PropertyRef = PropertyRef(
        "ephemeralStorage.sizeInGiB",
        description="The total amount, in GiB, of ephemeral storage to set for the task.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the task definition."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSTaskDefinitionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskDefinitionToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSTaskDefinition`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSTaskDefinitionToAWSAccountRelProperties = (
        ECSTaskDefinitionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskDefinitionToECSTaskRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskDefinitionToECSTaskRel(CartographyRelSchema):
    "Represents a `HAS_TASK_DEFINITION` relationship from `AWSECSTask` to `AWSECSTaskDefinition`."

    target_node_label: str = "AWSECSTask"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"task_definition_arn": PropertyRef("taskDefinitionArn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_TASK_DEFINITION"
    properties: ECSTaskDefinitionToECSTaskRelProperties = (
        ECSTaskDefinitionToECSTaskRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskDefinitionToTaskRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskDefinitionToTaskRoleRel(CartographyRelSchema):
    "Represents a `HAS_TASK_ROLE` relationship from `AWSECSTaskDefinition` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("taskRoleArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TASK_ROLE"
    properties: ECSTaskDefinitionToTaskRoleRelProperties = (
        ECSTaskDefinitionToTaskRoleRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskDefinitionToExecutionRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskDefinitionToExecutionRoleRel(CartographyRelSchema):
    "Represents a `HAS_EXECUTION_ROLE` relationship from `AWSECSTaskDefinition` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("executionRoleArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: ECSTaskDefinitionToExecutionRoleRelProperties = (
        ECSTaskDefinitionToExecutionRoleRelProperties()
    )


@dataclass(frozen=True)
class ECSTaskDefinitionSchema(CartographyNodeSchema):
    "Represents an `AWSECSTaskDefinition` node in the AWS graph."

    label: str = "AWSECSTaskDefinition"
    # DEPRECATED: legacy ECSTaskDefinition node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECSTaskDefinition"])
    properties: ECSTaskDefinitionNodeProperties = ECSTaskDefinitionNodeProperties()
    sub_resource_relationship: ECSTaskDefinitionToAWSAccountRel = (
        ECSTaskDefinitionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSTaskDefinitionToECSTaskRel(),
            ECSTaskDefinitionToTaskRoleRel(),
            ECSTaskDefinitionToExecutionRoleRel(),
        ]
    )
