from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher

# =============================================================================
# Shared relationship properties
# =============================================================================


@dataclass(frozen=True)
class AWSConfigToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


# =============================================================================
# AWSConfigurationRecorder
# =============================================================================


@dataclass(frozen=True)
class AWSConfigurationRecorderNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="A combination of name:account\\_id:region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    name: PropertyRef = PropertyRef("name", description="The name of the recorder.")
    role_arn: PropertyRef = PropertyRef(
        "role_arn",
        description="Amazon Resource Name (ARN) of the IAM role used to describe the AWS resources associated with the account.",
    )
    recording_group_all_supported: PropertyRef = PropertyRef(
        "recording_group_all_supported",
        description="Specifies whether AWS Config records configuration changes for every supported type of regional resource.",
    )
    recording_group_include_global_resource_types: PropertyRef = PropertyRef(
        "recording_group_include_global_resource_types",
        description="Specifies whether AWS Config includes all supported types of global resources (for example, IAM resources) with the resources that it records.",
    )
    recording_group_resource_types: PropertyRef = PropertyRef(
        "recording_group_resource_types",
        description="A comma-separated list that specifies the types of AWS resources for which AWS Config records configuration changes (for example, AWS::EC2::Instance or AWS::CloudTrail::Trail).",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The region of the configuration recorder.",
    )


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSConfigurationRecorder)
class AWSConfigurationRecorderToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSConfigurationRecorder`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSConfigToAWSAccountRelProperties = (
        AWSConfigToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSConfigurationRecorderSchema(CartographyNodeSchema):
    "Represents an `AWSConfigurationRecorder` node in the AWS graph."

    label: str = "AWSConfigurationRecorder"
    properties: AWSConfigurationRecorderNodeProperties = (
        AWSConfigurationRecorderNodeProperties()
    )
    sub_resource_relationship: AWSConfigurationRecorderToAWSAccountRel = (
        AWSConfigurationRecorderToAWSAccountRel()
    )


# =============================================================================
# AWSConfigDeliveryChannel
# =============================================================================


@dataclass(frozen=True)
class AWSConfigDeliveryChannelNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="A combination of name:account\\_id:region"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    name: PropertyRef = PropertyRef(
        "name", description="The name of the delivery channel."
    )
    s3_bucket_name: PropertyRef = PropertyRef(
        "s3_bucket_name",
        description="The name of the Amazon S3 bucket to which AWS Config delivers configuration snapshots and configuration history files.",
    )
    s3_key_prefix: PropertyRef = PropertyRef(
        "s3_key_prefix", description="The prefix for the specified Amazon S3 bucket."
    )
    s3_kms_key_arn: PropertyRef = PropertyRef(
        "s3_kms_key_arn",
        description="The Amazon Resource Name (ARN) of the AWS Key Management Service (KMS) customer managed key (CMK) used to encrypt objects delivered by AWS Config. Must belong to the same Region as the destination S3 bucket.",
    )
    sns_topic_arn: PropertyRef = PropertyRef(
        "sns_topic_arn",
        description="The Amazon Resource Name (ARN) of the Amazon SNS topic to which AWS Config sends notifications about configuration changes.",
    )
    config_snapshot_delivery_properties_delivery_frequency: PropertyRef = PropertyRef(
        "config_snapshot_delivery_properties_delivery_frequency",
        description="The frequency with which AWS Config delivers configuration snapshots.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the delivery channel."
    )


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSConfigDeliveryChannel)
class AWSConfigDeliveryChannelToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSConfigDeliveryChannel`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSConfigToAWSAccountRelProperties = (
        AWSConfigToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSConfigDeliveryChannelSchema(CartographyNodeSchema):
    "Represents an `AWSConfigDeliveryChannel` node in the AWS graph."

    label: str = "AWSConfigDeliveryChannel"
    properties: AWSConfigDeliveryChannelNodeProperties = (
        AWSConfigDeliveryChannelNodeProperties()
    )
    sub_resource_relationship: AWSConfigDeliveryChannelToAWSAccountRel = (
        AWSConfigDeliveryChannelToAWSAccountRel()
    )


# =============================================================================
# AWSConfigRule
# =============================================================================


@dataclass(frozen=True)
class AWSConfigRuleNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "ConfigRuleArn", description="The ARN of the config rule."
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )
    name: PropertyRef = PropertyRef(
        "ConfigRuleName", description="The name of the delivery channel."
    )
    description: PropertyRef = PropertyRef(
        "Description",
        description="The description that you provide for the AWS Config rule.",
    )
    arn: PropertyRef = PropertyRef(
        "ConfigRuleArn", description="The ARN of the config rule."
    )
    rule_id: PropertyRef = PropertyRef(
        "ConfigRuleId", description="The ID of the AWS Config rule."
    )
    scope_compliance_resource_types: PropertyRef = PropertyRef(
        "scope_compliance_resource_types",
        description="The resource types of only those AWS resources that you want to trigger an evaluation for the rule. You can only specify one type if you also specify a resource ID for ComplianceResourceId.",
    )
    scope_tag_key: PropertyRef = PropertyRef(
        "scope_tag_key",
        description="The tag key that is applied to only those AWS resources that you want to trigger an evaluation for the rule.",
    )
    scope_tag_value: PropertyRef = PropertyRef(
        "scope_tag_value",
        description="The tag value applied to only those AWS resources that you want to trigger an evaluation for the rule. If you specify a value for TagValue, you must also specify a value for TagKey.",
    )
    scope_tag_compliance_resource_id: PropertyRef = PropertyRef(
        "scope_tag_compliance_resource_id",
        description="The resource types of only those AWS resources that you want to trigger an evaluation for the rule. You can only specify one type if you also specify a resource ID for ComplianceResourceId.",
    )
    source_owner: PropertyRef = PropertyRef(
        "source_owner",
        description="Indicates whether AWS or the customer owns and manages the AWS Config rule.",
    )
    source_identifier: PropertyRef = PropertyRef(
        "source_identifier",
        description="For AWS Config managed rules, a predefined identifier from a list. For example, IAM\\_PASSWORD\\_POLICY is a managed rule.",
    )
    source_details: PropertyRef = PropertyRef(
        "source_details",
        description="Provides the source and type of the event that causes AWS Config to evaluate your AWS resources.",
    )
    input_parameters: PropertyRef = PropertyRef(
        "InputParameters",
        description="A string, in JSON format, that is passed to the AWS Config rule Lambda function.",
    )
    maximum_execution_frequency: PropertyRef = PropertyRef(
        "MaximumExecutionFrequency",
        description="The maximum frequency with which AWS Config runs evaluations for a rule.",
    )
    created_by: PropertyRef = PropertyRef(
        "CreatedBy",
        description="Service principal name of the service that created the rule.",
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The region of the delivery channel."
    )


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSConfigRule)
class AWSConfigRuleToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSConfigRule`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: AWSConfigToAWSAccountRelProperties = (
        AWSConfigToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class AWSConfigRuleSchema(CartographyNodeSchema):
    "Represents an `AWSConfigRule` node in the AWS graph."

    label: str = "AWSConfigRule"
    properties: AWSConfigRuleNodeProperties = AWSConfigRuleNodeProperties()
    sub_resource_relationship: AWSConfigRuleToAWSAccountRel = (
        AWSConfigRuleToAWSAccountRel()
    )
