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
class ElasticacheTopicNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("TopicArn", description="Same as ARN")
    arn: PropertyRef = PropertyRef(
        "TopicArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the SNS topic",
    )
    status: PropertyRef = PropertyRef(
        "TopicStatus", description="The status of the SNS topic (active, inactive)"
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ElasticacheTopicToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticacheTopicToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSElasticacheTopic`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ElasticacheTopicToAWSAccountRelProperties = (
        ElasticacheTopicToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ElasticacheTopicToElasticacheClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticacheTopicToElasticacheClusterRel(CartographyRelSchema):
    "Represents a `CACHE_CLUSTER` relationship from `AWSElasticacheTopic` to `AWSElasticacheCluster`."

    target_node_label: str = "AWSElasticacheCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cluster_arns", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CACHE_CLUSTER"
    properties: ElasticacheTopicToElasticacheClusterRelProperties = (
        ElasticacheTopicToElasticacheClusterRelProperties()
    )


@dataclass(frozen=True)
class ElasticacheTopicSchema(CartographyNodeSchema):
    "Represents an `AWSElasticacheTopic` node in the AWS graph."

    label: str = "AWSElasticacheTopic"
    # DEPRECATED: legacy ElasticacheTopic node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ElasticacheTopic"])
    properties: ElasticacheTopicNodeProperties = ElasticacheTopicNodeProperties()
    sub_resource_relationship: ElasticacheTopicToAWSAccountRel = (
        ElasticacheTopicToAWSAccountRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [ElasticacheTopicToElasticacheClusterRel()]
    )
