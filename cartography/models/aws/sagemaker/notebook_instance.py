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
    id: PropertyRef = PropertyRef("NotebookInstanceArn")
    arn: PropertyRef = PropertyRef("NotebookInstanceArn", extra_index=True)
    notebook_instance_name: PropertyRef = PropertyRef("NotebookInstanceName")
    notebook_instance_status: PropertyRef = PropertyRef("NotebookInstanceStatus")
    instance_type: PropertyRef = PropertyRef("InstanceType")
    url: PropertyRef = PropertyRef("Url")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_modified_time: PropertyRef = PropertyRef("LastModifiedTime")
    subnet_id: PropertyRef = PropertyRef("SubnetId")
    security_groups: PropertyRef = PropertyRef("SecurityGroups")
    role_arn: PropertyRef = PropertyRef("RoleArn")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    network_interface_id: PropertyRef = PropertyRef("NetworkInterfaceId")
    direct_internet_access: PropertyRef = PropertyRef("DirectInternetAccess")
    volume_size_in_gb: PropertyRef = PropertyRef("VolumeSizeInGB")
    root_access: PropertyRef = PropertyRef("RootAccess")
    platform_identifier: PropertyRef = PropertyRef("PlatformIdentifier")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class AWSSageMakerNotebookInstanceToAWSAccountRel(CartographyRelSchema):
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
