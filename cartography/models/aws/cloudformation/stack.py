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
class CloudFormationStackNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("StackId")
    arn: PropertyRef = PropertyRef("StackId", extra_index=True)
    stack_name: PropertyRef = PropertyRef("StackName")
    description: PropertyRef = PropertyRef("Description")
    stack_status: PropertyRef = PropertyRef("StackStatus")
    stack_status_reason: PropertyRef = PropertyRef("StackStatusReason")
    creation_time: PropertyRef = PropertyRef("CreationTime")
    last_updated_time: PropertyRef = PropertyRef("LastUpdatedTime")
    deletion_time: PropertyRef = PropertyRef("DeletionTime")
    disable_rollback: PropertyRef = PropertyRef("DisableRollback")
    rollback_configuration: PropertyRef = PropertyRef("RollbackConfiguration")
    timeout_in_minutes: PropertyRef = PropertyRef("TimeoutInMinutes")
    notification_arns: PropertyRef = PropertyRef("NotificationARNs")
    capabilities: PropertyRef = PropertyRef("Capabilities")
    parent_id: PropertyRef = PropertyRef("ParentId")
    root_id: PropertyRef = PropertyRef("RootId")
    change_set_id: PropertyRef = PropertyRef("ChangeSetId")
    drift_information: PropertyRef = PropertyRef("DriftInformation")
    tags: PropertyRef = PropertyRef("Tags")
    role_arn: PropertyRef = PropertyRef("RoleARN")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFormationStackToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudFormationStackToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
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
    target_node_label: str = "AWSRole"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("RoleARN")}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_EXECUTION_ROLE"
    properties: CloudFormationStackToRoleRelProperties = (
        CloudFormationStackToRoleRelProperties()
    )


@dataclass(frozen=True)
class CloudFormationStackSchema(CartographyNodeSchema):
    label: str = "CloudFormationStack"
    properties: CloudFormationStackNodeProperties = (
        CloudFormationStackNodeProperties()
    )
    sub_resource_relationship: CloudFormationStackToAWSAccountRel = (
        CloudFormationStackToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [CloudFormationStackToRoleRel()]
    )
