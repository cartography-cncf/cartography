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
from cartography.models.snowflake.extra_labels import SNOWFLAKE_SECURABLE


@dataclass(frozen=True)
class SnowflakeNotificationIntegrationNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="Account-scoped identifier for the notification integration."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    name: PropertyRef = PropertyRef(
        "name", extra_index=True, description="The notification integration name."
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Whether the integration may send or receive notifications.",
    )
    notification_hook_type: PropertyRef = PropertyRef(
        "notification_hook_type",
        description=(
            "Transport the integration uses: EMAIL, WEBHOOK, QUEUE_AWS_SNS_OUTBOUND, an "
            "Azure Event Grid queue or a GCP Pub/Sub queue."
        ),
    )
    aws_sns_topic_arn: PropertyRef = PropertyRef(
        "aws_sns_topic_arn",
        extra_index=True,
        description="ARN of the SNS topic Snowflake publishes notifications to.",
    )
    aws_sns_role_arn: PropertyRef = PropertyRef(
        "aws_sns_role_arn",
        extra_index=True,
        description="ARN of the AWS IAM role Snowflake assumes to publish to the topic.",
    )
    aws_sns_external_id: PropertyRef = PropertyRef(
        "aws_sns_external_id",
        description=(
            "External id the role's trust policy must require, which is what prevents "
            "another Snowflake account from assuming it."
        ),
    )
    azure_storage_queue_primary_uri: PropertyRef = PropertyRef(
        "azure_storage_queue_primary_uri",
        description="URI of the Azure storage queue that carries Event Grid notifications.",
    )
    azure_tenant_id: PropertyRef = PropertyRef(
        "azure_tenant_id",
        description="Entra ID tenant Snowflake requests an access token from for the queue.",
    )
    gcp_pubsub_subscription_name: PropertyRef = PropertyRef(
        "gcp_pubsub_subscription_name",
        extra_index=True,
        description="Full name of the Pub/Sub subscription Snowflake reads notifications from.",
    )
    gcp_pubsub_topic_name: PropertyRef = PropertyRef(
        "gcp_pubsub_topic_name",
        extra_index=True,
        description="Full name of the Pub/Sub topic Snowflake publishes notifications to.",
    )
    comment: PropertyRef = PropertyRef(
        "comment", description="Notification integration comment."
    )
    created_on: PropertyRef = PropertyRef(
        "created_on", description="When the notification integration was created."
    )


@dataclass(frozen=True)
class SnowflakeNotificationIntegrationToAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeAccount)-[:RESOURCE]->(:SnowflakeNotificationIntegration)
class SnowflakeNotificationIntegrationToAccountRel(CartographyRelSchema):
    """A Snowflake account contains the notification integration as a resource."""

    target_node_label: str = "SnowflakeAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ACCOUNT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: SnowflakeNotificationIntegrationToAccountRelProperties = (
        SnowflakeNotificationIntegrationToAccountRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotificationIntegrationToAWSPrincipalRelProperties(
    CartographyRelProperties
):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNotificationIntegration)-[:ASSUMES_ROLE]->(:AWSPrincipal)
class SnowflakeNotificationIntegrationToAWSPrincipalRel(CartographyRelSchema):
    """A Snowflake notification integration assumes an AWS IAM role to reach its SNS topic."""

    target_node_label: str = "AWSPrincipal"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_sns_role_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ASSUMES_ROLE"
    properties: SnowflakeNotificationIntegrationToAWSPrincipalRelProperties = (
        SnowflakeNotificationIntegrationToAWSPrincipalRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotificationIntegrationToSNSTopicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:SnowflakeNotificationIntegration)-[:NOTIFIES]->(:AWSSNSTopic)
class SnowflakeNotificationIntegrationToSNSTopicRel(CartographyRelSchema):
    """A Snowflake notification integration publishes to an Amazon SNS topic."""

    target_node_label: str = "AWSSNSTopic"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("aws_sns_topic_arn")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NOTIFIES"
    properties: SnowflakeNotificationIntegrationToSNSTopicRelProperties = (
        SnowflakeNotificationIntegrationToSNSTopicRelProperties()
    )


@dataclass(frozen=True)
class SnowflakeNotificationIntegrationSchema(CartographyNodeSchema):
    """Represents a Snowflake notification integration: the message queue or email hook Snowflake sends and receives events through."""

    label: str = "SnowflakeNotificationIntegration"
    properties: SnowflakeNotificationIntegrationNodeProperties = (
        SnowflakeNotificationIntegrationNodeProperties()
    )
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([SNOWFLAKE_SECURABLE])
    sub_resource_relationship: SnowflakeNotificationIntegrationToAccountRel = (
        SnowflakeNotificationIntegrationToAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            SnowflakeNotificationIntegrationToAWSPrincipalRel(),
            SnowflakeNotificationIntegrationToSNSTopicRel(),
        ],
    )
