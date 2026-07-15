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
class CloudTrailTrailNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "TrailARN", description="The ARN of the trail (same as arn)"
    )
    arn: PropertyRef = PropertyRef("TrailARN", description="The ARN of the trail")
    name: PropertyRef = PropertyRef(
        "Name", description="The name of the AWSCloudTrailTrail."
    )
    region: PropertyRef = PropertyRef(
        "Region", set_in_kwargs=True, description="The AWS region"
    )
    cloudwatch_logs_log_group_arn: PropertyRef = PropertyRef(
        "CloudWatchLogsLogGroupArn",
        description="The ARN identifier representing the log group where the AWSCloudTrailTrail delivers logs.",
    )
    cloudwatch_logs_role_arn: PropertyRef = PropertyRef(
        "CloudWatchLogsRoleArn",
        description="The role ARN that the AWSCloudTrailTrail's CloudWatch Logs endpoint assumes.",
    )
    event_selectors: PropertyRef = PropertyRef(
        "EventSelectors",
        description="JSON array of event selectors configured for the AWSCloudTrailTrail.",
    )
    advanced_event_selectors: PropertyRef = PropertyRef(
        "AdvancedEventSelectors",
        description="JSON array of advanced event selectors configured for the AWSCloudTrailTrail.",
    )
    has_custom_event_selectors: PropertyRef = PropertyRef(
        "HasCustomEventSelectors",
        description="Indicates if the AWSCloudTrailTrail has custom event selectors.",
    )
    has_insight_selectors: PropertyRef = PropertyRef(
        "HasInsightSelectors",
        description="Indicates if the AWSCloudTrailTrail has insight types specified.",
    )
    home_region: PropertyRef = PropertyRef(
        "HomeRegion", description="The Region where the AWSCloudTrailTrail was created."
    )
    include_global_service_events: PropertyRef = PropertyRef(
        "IncludeGlobalServiceEvents",
        description="Indicates if the AWSCloudTrailTrail includes AWS API calls from global services.",
    )
    is_multi_region_trail: PropertyRef = PropertyRef(
        "IsMultiRegionTrail",
        description="Indicates if the AWSCloudTrailTrail exists in one or all Regions.",
    )
    is_organization_trail: PropertyRef = PropertyRef(
        "IsOrganizationTrail",
        description="Indicates if the AWSCloudTrailTrail is an organization trail.",
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="The AWS KMS key ID that encrypts the AWSCloudTrailTrail's delivered logs.",
    )
    log_file_validation_enabled: PropertyRef = PropertyRef(
        "LogFileValidationEnabled",
        description="Indicates if log file validation is enabled for the AWSCloudTrailTrail.",
    )
    s3_bucket_name: PropertyRef = PropertyRef(
        "S3BucketName",
        description="The Amazon S3 bucket name where the AWSCloudTrailTrail delivers files.",
    )
    s3_key_prefix: PropertyRef = PropertyRef(
        "S3KeyPrefix",
        description="The S3 key prefix used after the bucket name for the AWSCloudTrailTrail's log files.",
    )
    sns_topic_arn: PropertyRef = PropertyRef(
        "SnsTopicARN",
        description="The ARN of the SNS topic used by the AWSCloudTrailTrail for delivery notifications.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class CloudTrailTrailToAwsAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSCloudTrailTrail`."

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
class CloudTrailTrailToS3BucketRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailTrailToS3BucketRel(CartographyRelSchema):
    "Represents a `LOGS_TO` relationship from `AWSCloudTrailTrail` to `AWSS3Bucket`."

    target_node_label: str = "AWSS3Bucket"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"name": PropertyRef("S3BucketName")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "LOGS_TO"
    properties: CloudTrailTrailToS3BucketRelProperties = (
        CloudTrailTrailToS3BucketRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailTrailToCloudWatchLogGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class CloudTrailTrailToCloudWatchLogGroupRel(CartographyRelSchema):
    "Represents a `SENDS_LOGS_TO_CLOUDWATCH` relationship from `AWSCloudTrailTrail` to `AWSCloudWatchLogGroup`."

    target_node_label: str = "AWSCloudWatchLogGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CloudWatchLogsLogGroupArn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "SENDS_LOGS_TO_CLOUDWATCH"
    properties: CloudTrailTrailToCloudWatchLogGroupRelProperties = (
        CloudTrailTrailToCloudWatchLogGroupRelProperties()
    )


@dataclass(frozen=True)
class CloudTrailTrailSchema(CartographyNodeSchema):
    "Represents an `AWSCloudTrailTrail` node in the AWS graph."

    label: str = "AWSCloudTrailTrail"
    # DEPRECATED: legacy CloudTrailTrail node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["CloudTrailTrail"])
    properties: CloudTrailTrailNodeProperties = CloudTrailTrailNodeProperties()
    sub_resource_relationship: CloudTrailToAWSAccountRel = CloudTrailToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            CloudTrailTrailToS3BucketRel(),
            CloudTrailTrailToCloudWatchLogGroupRel(),
        ]
    )
