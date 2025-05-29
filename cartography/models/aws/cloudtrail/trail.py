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
class CloudTrailTrailNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("TrailARN")
    arn: PropertyRef = PropertyRef("TrailARN")
    name: PropertyRef = PropertyRef("Name")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    cloudwatch_logs_log_group_arn: PropertyRef = PropertyRef(
        "CloudWatchLogsLogGroupArn"
    )
    cloudwatch_logs_role_arn: PropertyRef = PropertyRef("CloudWatchLogsRoleArn")
    has_custom_event_selectors: PropertyRef = PropertyRef("HasCustomEventSelectors")
    has_insight_selectors: PropertyRef = PropertyRef("HasInsightSelectors")
    home_region: PropertyRef = PropertyRef("HomeRegion")
    include_global_service_events: PropertyRef = PropertyRef(
        "IncludeGlobalServiceEvents"
    )
    is_multi_region_trail: PropertyRef = PropertyRef("IsMultiRegionTrail")
    is_organization_trail: PropertyRef = PropertyRef("IsOrganizationTrail")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    log_file_validation_enabled: PropertyRef = PropertyRef("LogFileValidationEnabled")
    s3_bucket_name: PropertyRef = PropertyRef("S3BucketName")
    s3_key_prefix: PropertyRef = PropertyRef("S3KeyPrefix")
    sns_topic_arn: PropertyRef = PropertyRef("SnsTopicARN")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailTrailToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: CloudTrailTrailToAwsAccountRelProperties = (
        CloudTrailTrailToAwsAccountRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailTrailToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailTrailToKMSKeyRel(CartographyRelSchema):
    target_node_label: str = "KMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("KmsKeyId"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: CloudTrailTrailToKMSKeyRelProperties = (
        CloudTrailTrailToKMSKeyRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailTrailToCloudWatchLogGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailTrailToCloudWatchLogGroupRel(CartographyRelSchema):
    target_node_label: str = "CloudWatchLogGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CloudWatchLogsLogGroupArn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SEND_LOGS_TO"
    properties: CloudTrailTrailToCloudWatchLogGroupRelProperties = (
        CloudTrailTrailToCloudWatchLogGroupRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailTrailSchema(CartographyNodeSchema):
    label: str = "CloudTrailTrail"
    properties: CloudTrailTrailNodeProperties = CloudTrailTrailNodeProperties()
    sub_resource_relationship: CloudTrailToAWSAccountRel = CloudTrailToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudTrailTrailToKMSKeyRel(),
            CloudTrailTrailToCloudWatchLogGroupRel(),
        ],
    )
