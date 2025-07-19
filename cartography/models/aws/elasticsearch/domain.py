from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import (
    CartographyNodeProperties,
    CartographyNodeSchema,
)
from cartography.models.core.relationships import (
    CartographyRelProperties,
    CartographyRelSchema,
    LinkDirection,
    make_target_node_matcher,
    OtherRelationships,
    TargetNodeMatcher,
)


@dataclass(frozen=True)
class ESDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DomainId")
    arn: PropertyRef = PropertyRef("ARN", extra_index=True)
    endpoint: PropertyRef = PropertyRef("Endpoint")
    created: PropertyRef = PropertyRef("created")
    deleted: PropertyRef = PropertyRef("Deleted")
    elasticsearch_version: PropertyRef = PropertyRef("ElasticsearchVersion")
    elasticsearch_cluster_config_instancetype: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfig.InstanceType"
    )
    elasticsearch_cluster_config_instancecount: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfig.InstanceCount"
    )
    elasticsearch_cluster_config_dedicatedmasterenabled: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfig.DedicatedMasterEnabled"
    )
    elasticsearch_cluster_config_zoneawarenessenabled: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfig.ZoneAwarenessEnabled"
    )
    elasticsearch_cluster_config_dedicatedmastertype: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfig.DedicatedMasterType"
    )
    elasticsearch_cluster_config_dedicatedmastercount: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfig.DedicatedMasterCount"
    )
    ebs_options_ebsenabled: PropertyRef = PropertyRef("EBSOptions.EBSEnabled")
    ebs_options_volumetype: PropertyRef = PropertyRef("EBSOptions.VolumeType")
    ebs_options_volumesize: PropertyRef = PropertyRef("EBSOptions.VolumeSize")
    ebs_options_iops: PropertyRef = PropertyRef("EBSOptions.Iops")
    encryption_at_rest_options_enabled: PropertyRef = PropertyRef(
        "EncryptionAtRestOptions.Enabled"
    )
    encryption_at_rest_options_kms_key_id: PropertyRef = PropertyRef(
        "EncryptionAtRestOptions.KmsKeyId"
    )
    log_publishing_options_cloudwatch_log_group_arn: PropertyRef = PropertyRef(
        "LogPublishingOptions.CloudWatchLogsLogGroupArn"
    )
    log_publishing_options_enabled: PropertyRef = PropertyRef(
        "LogPublishingOptions.Enabled"
    )
    exposed_internet: PropertyRef = PropertyRef("exposed_internet")
    subnet_ids: PropertyRef = PropertyRef("SubnetIds")
    security_group_ids: PropertyRef = PropertyRef("SecurityGroupIds")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
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
        {"id": PropertyRef("SubnetIds", one_to_many=True)}
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
        {"id": PropertyRef("SecurityGroupIds", one_to_many=True)}
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: ESDomainToEC2SecurityGroupRelProperties = (
        ESDomainToEC2SecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class ESDomainSchema(CartographyNodeSchema):
    label: str = "ESDomain"
    properties: ESDomainNodeProperties = ESDomainNodeProperties()
    sub_resource_relationship: ESDomainToAWSAccountRel = ESDomainToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ESDomainToEC2SubnetRel(),
            ESDomainToEC2SecurityGroupRel(),
        ]
    )
