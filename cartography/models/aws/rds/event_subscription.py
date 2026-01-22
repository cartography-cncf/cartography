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
class RDSEventSubscriptionNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("CustSubscriptionId")
    arn: PropertyRef = PropertyRef("EventSubscriptionArn", extra_index=True)
    customer_aws_id: PropertyRef = PropertyRef("CustomerAwsId")
    sns_topic_arn: PropertyRef = PropertyRef("SnsTopicArn")
    source_type: PropertyRef = PropertyRef("SourceType")
    status: PropertyRef = PropertyRef("Status")
    enabled: PropertyRef = PropertyRef("Enabled")
    subscription_creation_time: PropertyRef = PropertyRef("SubscriptionCreationTime")
    event_categories: PropertyRef = PropertyRef("event_categories", one_to_many=True)
    source_ids: PropertyRef = PropertyRef("source_ids", one_to_many=True)
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSEventSubscriptionToAWSAccountRel(CartographyRelSchema):
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
    target_node_label: str = "SNSTopic"
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
    target_node_label: str = "RDSInstance"
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
    target_node_label: str = "RDSCluster"
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
    target_node_label: str = "RDSSnapshot"
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
    label: str = "RDSEventSubscription"
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
