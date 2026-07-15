from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ElasticacheClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN", description="Same as ARN")
    arn: PropertyRef = PropertyRef(
        "ARN",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the ElastiCache cluster",
    )
    cache_cluster_id: PropertyRef = PropertyRef(
        "CacheClusterId", description="The unique identifier for the cache cluster"
    )
    cache_node_type: PropertyRef = PropertyRef(
        "CacheNodeType",
        description="The compute and memory capacity of the nodes in the cluster",
    )
    engine: PropertyRef = PropertyRef(
        "Engine", description="The name of the cache engine (redis, memcached)"
    )
    engine_version: PropertyRef = PropertyRef(
        "EngineVersion", description="The version of the cache engine"
    )
    cache_cluster_status: PropertyRef = PropertyRef(
        "CacheClusterStatus", description="The current state of the cache cluster"
    )
    num_cache_nodes: PropertyRef = PropertyRef(
        "NumCacheNodes", description="The number of cache nodes in the cluster"
    )
    preferred_availability_zone: PropertyRef = PropertyRef(
        "PreferredAvailabilityZone",
        description="The name of the Availability Zone in which the cache cluster is located",
    )
    preferred_maintenance_window: PropertyRef = PropertyRef(
        "PreferredMaintenanceWindow",
        description="The weekly time range during which maintenance on the cache cluster is performed",
    )
    cache_cluster_create_time: PropertyRef = PropertyRef(
        "CacheClusterCreateTime",
        description="The date and time when the cache cluster was created",
    )
    cache_subnet_group_name: PropertyRef = PropertyRef(
        "CacheSubnetGroupName",
        description="The name of the cache subnet group associated with the cache cluster",
    )
    auto_minor_version_upgrade: PropertyRef = PropertyRef(
        "AutoMinorVersionUpgrade",
        description="Indicates whether minor version patches are applied automatically",
    )
    replication_group_id: PropertyRef = PropertyRef(
        "ReplicationGroupId",
        description="The replication group to which this cache cluster belongs",
    )
    snapshot_retention_limit: PropertyRef = PropertyRef(
        "SnapshotRetentionLimit",
        description="The number of days for which ElastiCache will retain automatic cache cluster snapshots",
    )
    snapshot_window: PropertyRef = PropertyRef(
        "SnapshotWindow",
        description="The daily time range during which ElastiCache will take a snapshot of the cache cluster",
    )
    auth_token_enabled: PropertyRef = PropertyRef(
        "AuthTokenEnabled",
        description="Indicates whether an authentication token is enabled for the cache cluster",
    )
    transit_encryption_enabled: PropertyRef = PropertyRef(
        "TransitEncryptionEnabled",
        description="Indicates whether the cache cluster is encrypted in transit",
    )
    at_rest_encryption_enabled: PropertyRef = PropertyRef(
        "AtRestEncryptionEnabled",
        description="Indicates whether the cache cluster is encrypted at rest",
    )
    topic_arn: PropertyRef = PropertyRef(
        "TopicArn",
        description="The ARN of the SNS topic to which notifications are sent",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="The AWS region where the cache cluster is located",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class ElasticacheClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticacheClusterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSElasticacheCluster`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ElasticacheClusterToAWSAccountRelProperties = (
        ElasticacheClusterToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class ElasticacheClusterSchema(CartographyNodeSchema):
    "Represents an `AWSElasticacheCluster` node in the AWS graph."

    label: str = "AWSElasticacheCluster"
    # DEPRECATED: legacy ElasticacheCluster node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ElasticacheCluster"])
    properties: ElasticacheClusterNodeProperties = ElasticacheClusterNodeProperties()
    sub_resource_relationship: ElasticacheClusterToAWSAccountRel = (
        ElasticacheClusterToAWSAccountRel()
    )
