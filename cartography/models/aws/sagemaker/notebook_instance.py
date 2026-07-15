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
class AWSSageMakerNotebookInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "NotebookInstanceArn", description="The ARN of the Notebook Instance"
    )
    arn: PropertyRef = PropertyRef(
        "NotebookInstanceArn",
        extra_index=True,
        description="The ARN of the Notebook Instance",
    )
    notebook_instance_name: PropertyRef = PropertyRef(
        "NotebookInstanceName", description="The name of the Notebook Instance"
    )
    notebook_instance_status: PropertyRef = PropertyRef(
        "NotebookInstanceStatus", description="The status of the Notebook Instance"
    )
    instance_type: PropertyRef = PropertyRef(
        "InstanceType", description="The ML compute instance type"
    )
    url: PropertyRef = PropertyRef(
        "Url", description="The URL to connect to the Jupyter notebook"
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="When the Notebook Instance was created"
    )
    last_modified_time: PropertyRef = PropertyRef(
        "LastModifiedTime", description="When the Notebook Instance was last modified"
    )
    subnet_id: PropertyRef = PropertyRef(
        "SubnetId",
        description="Identifier of the subnet linked to this `AWSSageMakerNotebookInstance` node.",
    )
    security_groups: PropertyRef = PropertyRef(
        "SecurityGroups",
        description="Security group IDs attached to the notebook instance.",
    )
    role_arn: PropertyRef = PropertyRef(
        "RoleArn", description="The IAM role ARN associated with the instance"
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="Identifier of the KMS key linked to this `AWSSageMakerNotebookInstance` node.",
    )
    network_interface_id: PropertyRef = PropertyRef(
        "NetworkInterfaceId",
        description="Identifier of the network interface linked to this `AWSSageMakerNotebookInstance` node.",
    )
    direct_internet_access: PropertyRef = PropertyRef(
        "DirectInternetAccess",
        description="Whether the notebook instance has direct internet access.",
    )
    volume_size_in_gb: PropertyRef = PropertyRef(
        "VolumeSizeInGB",
        description="Size in GiB of the notebook instance's attached storage volume.",
    )
    root_access: PropertyRef = PropertyRef(
        "RootAccess",
        description="Whether notebook users have root access.",
    )
    platform_identifier: PropertyRef = PropertyRef(
        "PlatformIdentifier",
        description="SageMaker notebook platform version identifier.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the Notebook Instance exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSSageMakerNotebookInstance`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSSageMakerNotebookInstanceToAWSAccountRelProperties = (
        AWSSageMakerNotebookInstanceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToRoleRel(CartographyRelSchema):
    "Represents a `HAS_EXECUTION_ROLE` relationship from `AWSSageMakerNotebookInstance` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: AWSSageMakerNotebookInstanceToRoleRelProperties = (
        AWSSageMakerNotebookInstanceToRoleRelProperties()
    )


# Note: This relationship is probabilistic. It matches NotebookInstance to TrainingJob
# based on shared RoleArn, which indicates the notebook CAN invoke training jobs with
# that role, but doesn't definitively prove it actually did invoke that training job.
@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToTrainingJobRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToTrainingJobRel(CartographyRelSchema):
    "Represents a `CAN_INVOKE` relationship from `AWSSageMakerNotebookInstance` to `AWSSageMakerTrainingJob`."

    target_node_label: str = "AWSSageMakerTrainingJob"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"role_arn": PropertyRef("RoleArn")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CAN_INVOKE"
    properties: AWSSageMakerNotebookInstanceToTrainingJobRelProperties = (
        AWSSageMakerNotebookInstanceToTrainingJobRelProperties()
    )


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceSchema(CartographyNodeSchema):
    "Represents an `AWSSageMakerNotebookInstance` node in the AWS graph."

    label: str = "AWSSageMakerNotebookInstance"
    properties: AWSSageMakerNotebookInstanceNodeProperties = (
        AWSSageMakerNotebookInstanceNodeProperties()
    )
    sub_resource_relationship: AWSSageMakerNotebookInstanceToAWSAccountRel = (
        AWSSageMakerNotebookInstanceToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            AWSSageMakerNotebookInstanceToRoleRel(),
            AWSSageMakerNotebookInstanceToTrainingJobRel(),
        ]
    )
