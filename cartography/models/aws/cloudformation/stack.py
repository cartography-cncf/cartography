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
class CloudFormationStackNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "StackId", description="The unique identifier (ARN) of the CloudFormation Stack"
    )
    arn: PropertyRef = PropertyRef(
        "StackId",
        extra_index=True,
        description="The Amazon Resource Name (ARN) of the CloudFormation Stack",
    )
    stack_name: PropertyRef = PropertyRef(
        "StackName", description="The name of the stack"
    )
    description: PropertyRef = PropertyRef(
        "Description",
        description="A user-defined description associated with the stack",
    )
    stack_status: PropertyRef = PropertyRef(
        "StackStatus", description="Current status of the stack (e.g., CREATE_COMPLETE)"
    )
    stack_status_reason: PropertyRef = PropertyRef(
        "StackStatusReason",
        description="Success/failure message associated with the stack status",
    )
    creation_time: PropertyRef = PropertyRef(
        "CreationTime", description="The time at which the stack was created"
    )
    last_updated_time: PropertyRef = PropertyRef(
        "LastUpdatedTime", description="The time the stack was last updated"
    )
    role_arn: PropertyRef = PropertyRef(
        "RoleARN", description="The ARN of the IAM role used by CloudFormation"
    )
    parent_id: PropertyRef = PropertyRef(
        "ParentId", description="For nested stacks, the stack ID of the parent"
    )
    root_id: PropertyRef = PropertyRef(
        "RootId", description="For nested stacks, the stack ID of the root stack"
    )
    disable_rollback: PropertyRef = PropertyRef(
        "DisableRollback", description="Whether rollback is disabled"
    )
    tags: PropertyRef = PropertyRef(
        "Tags", description="A JSON string of tags associated with the stack"
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the stack exists",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class CloudFormationStackToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFormationStackToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSCloudFormationStack`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudFormationStackToAWSAccountRelProperties = (
        CloudFormationStackToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudFormationStackToRoleRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFormationStackToRoleRel(CartographyRelSchema):
    "Represents a `HAS_EXECUTION_ROLE` relationship from `AWSCloudFormationStack` to `AWSRole`."

    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleARN")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: CloudFormationStackToRoleRelProperties = (
        CloudFormationStackToRoleRelProperties()
    )


@dataclass(frozen=True)
class CloudFormationStackSchema(CartographyNodeSchema):
    "Represents an `AWSCloudFormationStack` node in the AWS graph."

    label: str = "AWSCloudFormationStack"
    # DEPRECATED: legacy CloudFormationStack node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CloudFormationStack"])
    properties: CloudFormationStackNodeProperties = CloudFormationStackNodeProperties()
    sub_resource_relationship: CloudFormationStackToAWSAccountRel = (
        CloudFormationStackToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CloudFormationStackToRoleRel()],
    )
