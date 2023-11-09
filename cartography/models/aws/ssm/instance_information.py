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
class SSMInstanceInformationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef('InstanceId')
    instance_id: PropertyRef = PropertyRef('InstanceId', extra_index=True)
    region: PropertyRef = PropertyRef('Region', set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)
    ping_status: PropertyRef = PropertyRef('PingStatus')
    last_ping_date_time: PropertyRef = PropertyRef('LastPingDateTime')
    agent_version: PropertyRef = PropertyRef('AgentVersion')
    is_latest_version: PropertyRef = PropertyRef('IsLatestVersion')
    platform_type: PropertyRef = PropertyRef('PlatformType')
    platform_name: PropertyRef = PropertyRef('PlatformName')
    platform_version: PropertyRef = PropertyRef('PlatformVersion')
    activation_id: PropertyRef = PropertyRef('ActivationId')
    iam_role: PropertyRef = PropertyRef('IamRole')
    registration_date: PropertyRef = PropertyRef('RegistrationDate')
    resource_type: PropertyRef = PropertyRef('ResourceType')
    name: PropertyRef = PropertyRef('Name')
    ip_address: PropertyRef = PropertyRef('IPAddress')
    computer_name: PropertyRef = PropertyRef('ComputerName')
    association_status: PropertyRef = PropertyRef('AssociationStatus')
    last_association_execution_date: PropertyRef = PropertyRef('LastAssociationExecutionDate')
    last_successful_association_execution_date: PropertyRef = PropertyRef('LastSuccessfulAssociationExecutionDate')
    source_id: PropertyRef = PropertyRef('SourceId')
    source_type: PropertyRef = PropertyRef('SourceType')


@dataclass(frozen=True)
class SSMInstanceInformationToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstanceInformationToAWSAccount(CartographyRelSchema):
    target_node_label: str = 'AWSAccount'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('AWS_ID', set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMInstanceInformationToAWSAccountRelProperties = SSMInstanceInformationToAWSAccountRelProperties()


@dataclass(frozen=True)
class SSMInstanceInformationToEC2InstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef('lastupdated', set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstanceInformationToEC2Instance(CartographyRelSchema):
    target_node_label: str = 'EC2Instance'
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {'id': PropertyRef('InstanceId')},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INFORMATION"
    properties: SSMInstanceInformationToEC2InstanceRelProperties = SSMInstanceInformationToEC2InstanceRelProperties()


@dataclass(frozen=True)
class SSMInstanceInformationSchema(CartographyNodeSchema):
    label: str = 'SSMInstanceInformation'
    properties: SSMInstanceInformationNodeProperties = SSMInstanceInformationNodeProperties()
    sub_resource_relationship: SSMInstanceInformationToAWSAccount = SSMInstanceInformationToAWSAccount()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSMInstanceInformationToEC2Instance(),
        ],
    )
