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
class ECSContainerDefinitionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id")
    task_definition_arn: PropertyRef = PropertyRef("_taskDefinitionArn")
    name: PropertyRef = PropertyRef("name")
    image: PropertyRef = PropertyRef("image")
    cpu: PropertyRef = PropertyRef("cpu")
    memory: PropertyRef = PropertyRef("memory")
    memory_reservation: PropertyRef = PropertyRef("memoryReservation")
    links: PropertyRef = PropertyRef("links")
    essential: PropertyRef = PropertyRef("essential")
    entry_point: PropertyRef = PropertyRef("entryPoint")
    command: PropertyRef = PropertyRef("command")
    start_timeout: PropertyRef = PropertyRef("startTimeout")
    stop_timeout: PropertyRef = PropertyRef("stop_timeout")
    hostname: PropertyRef = PropertyRef("hostname")
    user: PropertyRef = PropertyRef("user")
    working_directory: PropertyRef = PropertyRef("workingDirectory")
    disable_networking: PropertyRef = PropertyRef("disableNetworking")
    privileged: PropertyRef = PropertyRef("privileged")
    readonly_root_filesystem: PropertyRef = PropertyRef("readonlyRootFilesystem")
    dns_servers: PropertyRef = PropertyRef("dnsServers")
    dns_search_domains: PropertyRef = PropertyRef("dnsSearchDomains")
    docker_security_options: PropertyRef = PropertyRef("dockerSecurityOptions")
    interactive: PropertyRef = PropertyRef("interactive")
    pseudo_terminal: PropertyRef = PropertyRef("pseudoTerminal")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ECSContainerDefinitionToAWSAccountRelProperties = (
        ECSContainerDefinitionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerDefinitionToTaskDefinitionRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerDefinitionToTaskDefinitionRel(CartographyRelSchema):
    target_node_label: str = "ECSTaskDefinition"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("_taskDefinitionArn")}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONTAINER_DEFINITION"
    properties: ECSContainerDefinitionToTaskDefinitionRelProperties = (
        ECSContainerDefinitionToTaskDefinitionRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerDefinitionSchema(CartographyNodeSchema):
    label: str = "ECSContainerDefinition"
    properties: ECSContainerDefinitionNodeProperties = (
        ECSContainerDefinitionNodeProperties()
    )
    sub_resource_relationship: ECSContainerDefinitionToAWSAccountRel = (
        ECSContainerDefinitionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSContainerDefinitionToTaskDefinitionRel(),
        ]
    )
