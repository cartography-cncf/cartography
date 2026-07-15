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
class ECSContainerDefinitionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="The ARN of the task definition, plus the container definition name",
    )
    task_definition_arn: PropertyRef = PropertyRef(
        "_taskDefinitionArn",
        description="ARN of the task definition linked to this `AWSECSContainerDefinition` node.",
    )
    name: PropertyRef = PropertyRef("name", description="The name of a container.")
    image: PropertyRef = PropertyRef(
        "image",
        description="The image used to start a container. This string is passed directly to the Docker daemon.",
    )
    cpu: PropertyRef = PropertyRef(
        "cpu", description="The number of cpu units reserved for the container."
    )
    memory: PropertyRef = PropertyRef(
        "memory",
        description="The amount (in MiB) of memory to present to the container.",
    )
    memory_reservation: PropertyRef = PropertyRef(
        "memoryReservation",
        description="The soft limit (in MiB) of memory to reserve for the container.",
    )
    links: PropertyRef = PropertyRef(
        "links",
        description="The links parameter allows containers to communicate with each other without the need for port mappings.",
    )
    essential: PropertyRef = PropertyRef(
        "essential",
        description="If the essential parameter of a container is marked as true, and that container fails or stops for any reason, all other containers that are part of the task are stopped.",
    )
    entry_point: PropertyRef = PropertyRef(
        "entryPoint", description="The entry point that's passed to the container."
    )
    command: PropertyRef = PropertyRef(
        "command", description="The command that's passed to the container."
    )
    start_timeout: PropertyRef = PropertyRef(
        "startTimeout",
        description="Time duration (in seconds) to wait before giving up on resolving dependencies for a container.",
    )
    stop_timeout: PropertyRef = PropertyRef(
        "stop_timeout",
        description="Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own.",
    )
    hostname: PropertyRef = PropertyRef(
        "hostname", description="The hostname to use for your container."
    )
    user: PropertyRef = PropertyRef(
        "user", description="The user to use inside the container."
    )
    working_directory: PropertyRef = PropertyRef(
        "workingDirectory",
        description="The working directory to run commands inside the container in.",
    )
    disable_networking: PropertyRef = PropertyRef(
        "disableNetworking",
        description="When this parameter is true, networking is disabled within the container.",
    )
    privileged: PropertyRef = PropertyRef(
        "privileged",
        description="When this parameter is true, the container is given elevated privileges on the host container instance (similar to the root user).",
    )
    readonly_root_filesystem: PropertyRef = PropertyRef(
        "readonlyRootFilesystem",
        description="When this parameter is true, the container is given read-only access to its root file system.",
    )
    dns_servers: PropertyRef = PropertyRef(
        "dnsServers",
        description="A list of DNS servers that are presented to the container.",
    )
    dns_search_domains: PropertyRef = PropertyRef(
        "dnsSearchDomains",
        description="A list of DNS search domains that are presented to the container.",
    )
    docker_security_options: PropertyRef = PropertyRef(
        "dockerSecurityOptions",
        description="A list of strings to provide custom labels for SELinux and AppArmor multi-level security systems. This field isn't valid for containers in tasks using the Fargate launch type.",
    )
    interactive: PropertyRef = PropertyRef(
        "interactive",
        description="When this parameter is true, you can deploy containerized applications that require stdin or a tty to be allocated.",
    )
    pseudo_terminal: PropertyRef = PropertyRef(
        "pseudoTerminal", description="When this parameter is true, a TTY is allocated."
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the container definition.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerDefinitionToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSECSContainerDefinition`."

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
    "Represents a `HAS_CONTAINER_DEFINITION` relationship from `AWSECSTaskDefinition` to `AWSECSContainerDefinition`."

    target_node_label: str = "AWSECSTaskDefinition"
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
    "Represents an `AWSECSContainerDefinition` node in the AWS graph."

    label: str = "AWSECSContainerDefinition"
    # DEPRECATED: legacy ECSContainerDefinition node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ECSContainerDefinition"])
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
