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
class ESDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DomainId")
    domainid: PropertyRef = PropertyRef("DomainId", extra_index=True)
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    deleted: PropertyRef = PropertyRef("Deleted")
    created: PropertyRef = PropertyRef("Created")
    endpoint: PropertyRef = PropertyRef("Endpoint")
    elasticsearch_version: PropertyRef = PropertyRef("ElasticsearchVersion")
    # Cluster config properties (flattened)
    elasticsearch_cluster_config_instancetype: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigInstanceType"
    )
    elasticsearch_cluster_config_instancecount: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigInstanceCount"
    )
    elasticsearch_cluster_config_dedicatedmasterenabled: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigDedicatedMasterEnabled"
    )
    elasticsearch_cluster_config_zoneawarenessenabled: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigZoneAwarenessEnabled"
    )
    elasticsearch_cluster_config_dedicatedmastertype: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigDedicatedMasterType"
    )
    elasticsearch_cluster_config_dedicatedmastercount: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigDedicatedMasterCount"
    )
    # EBS options (flattened)
    ebs_options_ebsenabled: PropertyRef = PropertyRef("EBSOptionsEBSEnabled")
    ebs_options_volumetype: PropertyRef = PropertyRef("EBSOptionsVolumeType")
    ebs_options_volumesize: PropertyRef = PropertyRef("EBSOptionsVolumeSize")
    ebs_options_iops: PropertyRef = PropertyRef("EBSOptionsIops")
    # Encryption options (flattened)
    encryption_at_rest_options_enabled: PropertyRef = PropertyRef(
        "EncryptionAtRestOptionsEnabled"
    )
    encryption_at_rest_options_kms_key_id: PropertyRef = PropertyRef(
        "EncryptionAtRestOptionsKmsKeyId"
    )
    # Log publishing options (flattened)
    log_publishing_options_cloudwatch_log_group_arn: PropertyRef = PropertyRef(
        "LogPublishingOptionsCloudWatchLogsLogGroupArn"
    )
    log_publishing_options_enabled: PropertyRef = PropertyRef(
        "LogPublishingOptionsEnabled"
    )


@dataclass(frozen=True)
class ESDomainToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ESDomainToAWSAccountRelProperties = ESDomainToAWSAccountRelProperties()


@dataclass(frozen=True)
class ESDomainToEC2SubnetRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainToEC2SubnetRel(CartographyRelSchema):
    target_node_label: str = "EC2Subnet"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SubnetIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PART_OF_SUBNET"
    properties: ESDomainToEC2SubnetRelProperties = ESDomainToEC2SubnetRelProperties()


@dataclass(frozen=True)
class ESDomainToEC2SecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainToEC2SecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("SecurityGroupIds", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: ESDomainToEC2SecurityGroupRelProperties = (
        ESDomainToEC2SecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class ESDomainSchema(CartographyNodeSchema):
    """
    Elasticsearch domain schema.

    For domains with multiple subnets or security groups, the data should be
    flattened so each combination is a separate row.
    """

    label: str = "ESDomain"
    properties: ESDomainNodeProperties = ESDomainNodeProperties()
    sub_resource_relationship: ESDomainToAWSAccountRel = ESDomainToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ESDomainToEC2SubnetRel(),
            ESDomainToEC2SecurityGroupRel(),
        ],
    )
