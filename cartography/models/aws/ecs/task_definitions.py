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
class ECSTaskDefinitionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("taskDefinitionArn")
    arn: PropertyRef = PropertyRef("taskDefinitionArn", extra_index=True)
    family: PropertyRef = PropertyRef("family")
    task_role_arn: PropertyRef = PropertyRef("taskRoleArn")
    execution_role_arn: PropertyRef = PropertyRef("executionRoleArn")
    network_mode: PropertyRef = PropertyRef("networkMode")
    revision: PropertyRef = PropertyRef("revision")
    status: PropertyRef = PropertyRef("status")
    compatibilities: PropertyRef = PropertyRef("compatibilities")
    runtime_platform_cpu_architecture: PropertyRef = PropertyRef(
        "runtimePlatform.cpuArchitecture"
    )
    runtime_platform_operating_system_family: PropertyRef = PropertyRef(
        "runtimePlatform.operatingSystemFamily"
    )
    requires_compatibilities: PropertyRef = PropertyRef("requiresCompatibilities")
    cpu: PropertyRef = PropertyRef("cpu")
    memory: PropertyRef = PropertyRef("memory")
    pid_mode: PropertyRef = PropertyRef("pidMode")
    ipc_mode: PropertyRef = PropertyRef("ipcMode")
    proxy_configuration_type: PropertyRef = PropertyRef("proxyConfiguration.type")
    proxy_configuration_container_name: PropertyRef = PropertyRef(
        "proxyConfiguration.containerName"
    )
    registered_at: PropertyRef = PropertyRef("registeredAt")
    deregistered_at: PropertyRef = PropertyRef("deregisteredAt")
    registered_by: PropertyRef = PropertyRef("registeredBy")
    ephemeral_storage_size_in_gib: PropertyRef = PropertyRef(
        "ephemeralStorage.sizeInGiB"
    )
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskDefinitionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSTaskDefinitionToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "ECSTask"
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
    label: str = "ECSTaskDefinition"
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
