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
class SSMInstanceInformationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "InstanceId", description="The ARN of the instance information"
    )
    instance_id: PropertyRef = PropertyRef(
        "InstanceId", extra_index=True, description="The managed node ID."
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the instance information.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    ping_status: PropertyRef = PropertyRef(
        "PingStatus", description="Connection status of SSM Agent."
    )
    last_ping_date_time: PropertyRef = PropertyRef(
        "LastPingDateTime",
        description="The date and time when the agent last pinged the Systems Manager service.",
    )
    agent_version: PropertyRef = PropertyRef(
        "AgentVersion",
        description="The version of SSM Agent running on your Linux managed node.",
    )
    is_latest_version: PropertyRef = PropertyRef(
        "IsLatestVersion",
        description="Indicates whether the latest version of SSM Agent is running on your Linux managed node. This field doesn't indicate whether or not the latest version is installed on Windows managed nodes, because some older versions of Windows Server use the EC2Config service to process Systems Manager requests.",
    )
    platform_type: PropertyRef = PropertyRef(
        "PlatformType", description="The operating system platform type."
    )
    platform_name: PropertyRef = PropertyRef(
        "PlatformName",
        description="The name of the operating system platform running on your managed node.",
    )
    platform_version: PropertyRef = PropertyRef(
        "PlatformVersion",
        description="The version of the OS platform running on your managed node.",
    )
    activation_id: PropertyRef = PropertyRef(
        "ActivationId",
        description="The activation ID created by AWS Systems Manager when the server or virtual machine (VM) was registered.",
    )
    iam_role: PropertyRef = PropertyRef(
        "IamRole",
        description="The AWS Identity and Access Management (IAM) role assigned to the on-premises Systems Manager managed node. This call doesn't return the IAM role for Amazon Elastic Compute Cloud (Amazon EC2) instances.",
    )
    registration_date: PropertyRef = PropertyRef(
        "RegistrationDate",
        description="The date the server or VM was registered with AWS as a managed node.",
    )
    resource_type: PropertyRef = PropertyRef(
        "ResourceType",
        description="The type of instance. Instances are either EC2 instances or managed instances.",
    )
    name: PropertyRef = PropertyRef(
        "Name",
        description="The name assigned to an on-premises server, edge device, or virtual machine (VM) when it is activated as a Systems Manager managed node. The name is specified as the DefaultInstanceName property using the CreateActivation command.",
    )
    ip_address: PropertyRef = PropertyRef(
        "IPAddress", description="The IP address of the managed node."
    )
    computer_name: PropertyRef = PropertyRef(
        "ComputerName", description="The fully qualified host name of the managed node."
    )
    association_status: PropertyRef = PropertyRef(
        "AssociationStatus", description="The status of the association."
    )
    last_association_execution_date: PropertyRef = PropertyRef(
        "LastAssociationExecutionDate",
        description="The date the association was last run.",
    )
    last_successful_association_execution_date: PropertyRef = PropertyRef(
        "LastSuccessfulAssociationExecutionDate",
        description="The last date the association was successfully run.",
    )
    source_id: PropertyRef = PropertyRef(
        "SourceId",
        description="The ID of the source resource. For AWS IoT Greengrass devices, SourceId is the Thing name.",
    )
    source_type: PropertyRef = PropertyRef(
        "SourceType",
        description="The type of the source resource. For AWS IoT Greengrass devices, SourceType is AWS::IoT::Thing.",
    )


@dataclass(frozen=True)
class SSMInstanceInformationToAWSAccountRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstanceInformationToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSSMInstanceInformation`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SSMInstanceInformationToAWSAccountRelRelProperties = (
        SSMInstanceInformationToAWSAccountRelRelProperties()
    )


@dataclass(frozen=True)
class SSMInstanceInformationToEC2InstanceRelRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class SSMInstanceInformationToEC2InstanceRel(CartographyRelSchema):
    "Represents a `HAS_INFORMATION` relationship from `AWSEC2Instance` to `AWSSSMInstanceInformation`."

    target_node_label: str = "AWSEC2Instance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("InstanceId")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_INFORMATION"
    properties: SSMInstanceInformationToEC2InstanceRelRelProperties = (
        SSMInstanceInformationToEC2InstanceRelRelProperties()
    )


@dataclass(frozen=True)
class SSMInstanceInformationSchema(CartographyNodeSchema):
    "Represents an `AWSSSMInstanceInformation` node in the AWS graph."

    label: str = "AWSSSMInstanceInformation"
    # DEPRECATED: legacy SSMInstanceInformation node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["SSMInstanceInformation"])
    properties: SSMInstanceInformationNodeProperties = (
        SSMInstanceInformationNodeProperties()
    )
    sub_resource_relationship: SSMInstanceInformationToAWSAccountRel = (
        SSMInstanceInformationToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SSMInstanceInformationToEC2InstanceRel(),
        ],
    )
