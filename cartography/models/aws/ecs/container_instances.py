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
class ECSContainerInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("containerInstanceArn")
    arn: PropertyRef = PropertyRef("containerInstanceArn", extra_index=True)
    ec2_instance_id: PropertyRef = PropertyRef("ec2InstanceId")
    capacity_provider_name: PropertyRef = PropertyRef("capacityProviderName")
    version: PropertyRef = PropertyRef("version")
    version_info_agent_version: PropertyRef = PropertyRef("versionInfo.agentVersion")
    version_info_agent_hash: PropertyRef = PropertyRef("versionInfo.agentHash")
    version_info_agent_docker_version: PropertyRef = PropertyRef(
        "versionInfo.dockerVersion"
    )
    status: PropertyRef = PropertyRef("status")
    status_reason: PropertyRef = PropertyRef("statusReason")
    agent_connected: PropertyRef = PropertyRef("agentConnected")
    agent_update_status: PropertyRef = PropertyRef("agentUpdateStatus")
    registered_at: PropertyRef = PropertyRef("registeredAt")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ECSContainerInstanceToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "ECSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ClusterArn", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_CONTAINER_INSTANCE"
    properties: ECSContainerInstanceToECSClusterRelProperties = (
        ECSContainerInstanceToECSClusterRelProperties()
    )


@dataclass(frozen=True)
class ECSContainerInstanceSchema(CartographyNodeSchema):
    label: str = "ECSContainerInstance"
    properties: ECSContainerInstanceNodeProperties = (
        ECSContainerInstanceNodeProperties()
    )
    sub_resource_relationship: ECSContainerInstanceToAWSAccountRel = (
        ECSContainerInstanceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ECSContainerInstanceToECSClusterRel(),
        ]
    )
