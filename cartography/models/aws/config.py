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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    role_arn: PropertyRef = PropertyRef("role_arn")
    recording_group_all_supported: PropertyRef = PropertyRef(
        "recording_group_all_supported"
    )
    recording_group_include_global_resource_types: PropertyRef = PropertyRef(
        "recording_group_include_global_resource_types",
    )
    recording_group_resource_types: PropertyRef = PropertyRef(
        "recording_group_resource_types"
    )
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSConfigurationRecorder)
class AWSConfigurationRecorderToAWSAccountRel(CartographyRelSchema):
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
    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("name")
    s3_bucket_name: PropertyRef = PropertyRef("s3_bucket_name")
    s3_key_prefix: PropertyRef = PropertyRef("s3_key_prefix")
    s3_kms_key_arn: PropertyRef = PropertyRef("s3_kms_key_arn")
    sns_topic_arn: PropertyRef = PropertyRef("sns_topic_arn")
    config_snapshot_delivery_properties_delivery_frequency: PropertyRef = PropertyRef(
        "config_snapshot_delivery_properties_delivery_frequency",
    )
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSConfigDeliveryChannel)
class AWSConfigDeliveryChannelToAWSAccountRel(CartographyRelSchema):
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
    id: PropertyRef = PropertyRef("ConfigRuleArn")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef("ConfigRuleName")
    description: PropertyRef = PropertyRef("Description")
    arn: PropertyRef = PropertyRef("ConfigRuleArn")
    rule_id: PropertyRef = PropertyRef("ConfigRuleId")
    scope_compliance_resource_types: PropertyRef = PropertyRef(
        "scope_compliance_resource_types"
    )
    scope_tag_key: PropertyRef = PropertyRef("scope_tag_key")
    scope_tag_value: PropertyRef = PropertyRef("scope_tag_value")
    scope_tag_compliance_resource_id: PropertyRef = PropertyRef(
        "scope_tag_compliance_resource_id"
    )
    source_owner: PropertyRef = PropertyRef("source_owner")
    source_identifier: PropertyRef = PropertyRef("source_identifier")
    source_details: PropertyRef = PropertyRef("source_details")
    input_parameters: PropertyRef = PropertyRef("InputParameters")
    maximum_execution_frequency: PropertyRef = PropertyRef("MaximumExecutionFrequency")
    created_by: PropertyRef = PropertyRef("CreatedBy")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)


@dataclass(frozen=True)
# (:AWSAccount)-[:RESOURCE]->(:AWSConfigRule)
class AWSConfigRuleToAWSAccountRel(CartographyRelSchema):
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
    label: str = "AWSConfigRule"
    properties: AWSConfigRuleNodeProperties = AWSConfigRuleNodeProperties()
    sub_resource_relationship: AWSConfigRuleToAWSAccountRel = (
        AWSConfigRuleToAWSAccountRel()
    )
