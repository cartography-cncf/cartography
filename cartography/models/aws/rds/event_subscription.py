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
class RDSEventSubscriptionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "CustSubscriptionId", description="The customer subscription identifier"
    )
    arn: PropertyRef = PropertyRef(
        "EventSubscriptionArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the event subscription",
    )
    customer_aws_id: PropertyRef = PropertyRef(
        "CustomerAwsId",
        description="The AWS customer account associated with the event subscription",
    )
    sns_topic_arn: PropertyRef = PropertyRef(
        "SnsTopicArn",
        description="The ARN of the SNS topic to which notifications are sent",
    )
    source_type: PropertyRef = PropertyRef(
        "SourceType",
        description="The type of source that is generating the events (db-instance, db-cluster, db-snapshot)",
    )
    status: PropertyRef = PropertyRef(
        "Status", description="The status of the event subscription (active, inactive)"
    )
    enabled: PropertyRef = PropertyRef(
        "Enabled", description="Whether the event subscription is enabled"
    )
    subscription_creation_time: PropertyRef = PropertyRef(
        "SubscriptionCreationTime",
        description="The time the event subscription was created",
    )
    event_categories: PropertyRef = PropertyRef(
        "event_categories",
        one_to_many=True,
        description="List of event categories for which to receive notifications",
    )
    source_ids: PropertyRef = PropertyRef(
        "source_ids",
        one_to_many=True,
        description="List of source identifiers for which to receive notifications",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the event subscription is located",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class RDSEventSubscriptionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSRDSEventSubscription`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RDSEventSubscriptionToAWSAccountRelProperties = (
        RDSEventSubscriptionToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RDSEventSubscriptionToSNSTopicRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToSNSTopicRel(CartographyRelSchema):
    "Represents a `NOTIFIES` relationship from `AWSRDSEventSubscription` to `AWSSNSTopic`."

    target_node_label: str = "AWSSNSTopic"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "arn": PropertyRef("SnsTopicArn"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "NOTIFIES"
    properties: RDSEventSubscriptionToSNSTopicRelProperties = (
        RDSEventSubscriptionToSNSTopicRelProperties()
    )


@dataclass(frozen=True)
class RDSEventSubscriptionToRDSInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToRDSInstanceRel(CartographyRelSchema):
    "Represents a `MONITORS` relationship from `AWSRDSEventSubscription` to `AWSRDSInstance`."

    target_node_label: str = "AWSRDSInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_instance_identifier": PropertyRef("source_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: RDSEventSubscriptionToRDSInstanceRelProperties = (
        RDSEventSubscriptionToRDSInstanceRelProperties()
    )


@dataclass(frozen=True)
class RDSEventSubscriptionToRDSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToRDSClusterRel(CartographyRelSchema):
    "Represents a `MONITORS` relationship from `AWSRDSEventSubscription` to `AWSRDSCluster`."

    target_node_label: str = "AWSRDSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_cluster_identifier": PropertyRef("source_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: RDSEventSubscriptionToRDSClusterRelProperties = (
        RDSEventSubscriptionToRDSClusterRelProperties()
    )


@dataclass(frozen=True)
class RDSEventSubscriptionToRDSSnapshotRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToRDSSnapshotRel(CartographyRelSchema):
    "Represents a `MONITORS` relationship from `AWSRDSEventSubscription` to `AWSRDSSnapshot`."

    target_node_label: str = "AWSRDSSnapshot"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_snapshot_identifier": PropertyRef("source_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MONITORS"
    properties: RDSEventSubscriptionToRDSSnapshotRelProperties = (
        RDSEventSubscriptionToRDSSnapshotRelProperties()
    )


@dataclass(frozen=True)
class RDSEventSubscriptionSchema(CartographyNodeSchema):
    "Represents an `AWSRDSEventSubscription` node in the AWS graph."

    label: str = "AWSRDSEventSubscription"
    # DEPRECATED: legacy RDSEventSubscription node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["RDSEventSubscription"])
    properties: RDSEventSubscriptionNodeProperties = (
        RDSEventSubscriptionNodeProperties()
    )
    sub_resource_relationship: RDSEventSubscriptionToAWSAccountRel = (
        RDSEventSubscriptionToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RDSEventSubscriptionToSNSTopicRel(),
            RDSEventSubscriptionToRDSInstanceRel(),
            RDSEventSubscriptionToRDSClusterRel(),
            RDSEventSubscriptionToRDSSnapshotRel(),
        ]
    )
