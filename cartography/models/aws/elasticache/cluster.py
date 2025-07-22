from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class ElasticacheClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("ARN")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    cache_cluster_id: PropertyRef = PropertyRef("CacheClusterId")
    cache_node_type: PropertyRef = PropertyRef("CacheNodeType")
    engine: PropertyRef = PropertyRef("Engine")
    engine_version: PropertyRef = PropertyRef("EngineVersion")
    cache_cluster_status: PropertyRef = PropertyRef("CacheClusterStatus")
    num_cache_nodes: PropertyRef = PropertyRef("NumCacheNodes")
    preferred_availability_zone: PropertyRef = PropertyRef("PreferredAvailabilityZone")
    preferred_maintenance_window: PropertyRef = PropertyRef(
        "PreferredMaintenanceWindow"
    )
    cache_cluster_create_time: PropertyRef = PropertyRef("CacheClusterCreateTime")
    cache_subnet_group_name: PropertyRef = PropertyRef("CacheSubnetGroupName")
    auto_minor_version_upgrade: PropertyRef = PropertyRef("AutoMinorVersionUpgrade")
    replication_group_id: PropertyRef = PropertyRef("ReplicationGroupId")
    snapshot_retention_limit: PropertyRef = PropertyRef("SnapshotRetentionLimit")
    snapshot_window: PropertyRef = PropertyRef("SnapshotWindow")
    auth_token_enabled: PropertyRef = PropertyRef("AuthTokenEnabled")
    transit_encryption_enabled: PropertyRef = PropertyRef("TransitEncryptionEnabled")
    at_rest_encryption_enabled: PropertyRef = PropertyRef("AtRestEncryptionEnabled")
    topic_arn: PropertyRef = PropertyRef("TopicArn")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticacheClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ElasticacheClusterToAWSAccountRel(CartographyRelSchema):
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
    label: str = "ElasticacheCluster"
    properties: ElasticacheClusterNodeProperties = ElasticacheClusterNodeProperties()
    sub_resource_relationship: ElasticacheClusterToAWSAccountRel = (
        ElasticacheClusterToAWSAccountRel()
    )
