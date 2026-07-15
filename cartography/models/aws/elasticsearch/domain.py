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
class ESDomainNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "DomainId", description="Unique identifier for this `AWSESDomain` node."
    )
    domainid: PropertyRef = PropertyRef(
        "DomainId",
        extra_index=True,
        description="Identifier of the domain linked to this `AWSESDomain` node.",
    )
    arn: PropertyRef = PropertyRef(
        "ARN",
        extra_index=True,
        description="Amazon Resource Name (ARN) of this `AWSESDomain` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that updated this `AWSESDomain` node.",
    )
    deleted: PropertyRef = PropertyRef(
        "Deleted", description="Whether this `AWSESDomain` node is marked as deleted."
    )
    created: PropertyRef = PropertyRef(
        "Created", description="Whether this `AWSESDomain` node has been created."
    )
    endpoint: PropertyRef = PropertyRef(
        "Endpoint", description="Network endpoint used to access the search domain."
    )
    name: PropertyRef = PropertyRef(
        "DomainName", extra_index=True, description="Name of this `AWSESDomain` node."
    )
    elasticsearch_version: PropertyRef = PropertyRef(
        "ElasticsearchVersion",
        description="Elasticsearch engine version running on the domain.",
    )
    engine: PropertyRef = PropertyRef(
        "Engine", description="Search engine family running on the domain."
    )
    exposed_internet: PropertyRef = PropertyRef(
        "exposed_internet",
        description="Whether this `AWSESDomain` node is exposed to the public internet.",
    )
    # Cluster config properties (flattened)
    elasticsearch_cluster_config_instancetype: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigInstanceType",
        description="EC2 instance type used by data nodes in the search cluster.",
    )
    elasticsearch_cluster_config_instancecount: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigInstanceCount",
        description="Number of data-node instances in the search cluster.",
    )
    elasticsearch_cluster_config_dedicatedmasterenabled: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigDedicatedMasterEnabled",
        description="Whether elasticsearch cluster config dedicated master is enabled for this `AWSESDomain` node.",
    )
    elasticsearch_cluster_config_zoneawarenessenabled: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigZoneAwarenessEnabled",
        description="Whether elasticsearch cluster config zone awareness is enabled for this `AWSESDomain` node.",
    )
    elasticsearch_cluster_config_dedicatedmastertype: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigDedicatedMasterType",
        description="EC2 instance type used by dedicated master nodes.",
    )
    elasticsearch_cluster_config_dedicatedmastercount: PropertyRef = PropertyRef(
        "ElasticsearchClusterConfigDedicatedMasterCount",
        description="Number of dedicated master nodes in the search cluster.",
    )
    # EBS options (flattened)
    ebs_options_ebsenabled: PropertyRef = PropertyRef(
        "EBSOptionsEBSEnabled",
        description="Whether ebs options ebs is enabled for this `AWSESDomain` node.",
    )
    ebs_options_volumetype: PropertyRef = PropertyRef(
        "EBSOptionsVolumeType",
        description="EBS volume type attached to each search data node.",
    )
    ebs_options_volumesize: PropertyRef = PropertyRef(
        "EBSOptionsVolumeSize",
        description="EBS storage size in GiB allocated to each search data node.",
    )
    ebs_options_iops: PropertyRef = PropertyRef(
        "EBSOptionsIops",
        description="Provisioned IOPS configured for each search data-node volume.",
    )
    # Encryption options (flattened)
    encryption_at_rest_options_enabled: PropertyRef = PropertyRef(
        "EncryptionAtRestOptionsEnabled",
        description="Whether encryption at rest options is enabled for this `AWSESDomain` node.",
    )
    encryption_at_rest_options_kms_key_id: PropertyRef = PropertyRef(
        "EncryptionAtRestOptionsKmsKeyId",
        description="Identifier of the encryption at rest options KMS key linked to this `AWSESDomain` node.",
    )
    # Log publishing options (per log type)
    log_publishing_index_slow_logs_enabled: PropertyRef = PropertyRef(
        "LogPublishingIndexSlowLogsEnabled",
        description="Whether log publishing index slow logs is enabled for this `AWSESDomain` node.",
    )
    log_publishing_index_slow_logs_arn: PropertyRef = PropertyRef(
        "LogPublishingIndexSlowLogsArn",
        description="ARN of the log publishing index slow logs linked to this `AWSESDomain` node.",
    )
    log_publishing_search_slow_logs_enabled: PropertyRef = PropertyRef(
        "LogPublishingSearchSlowLogsEnabled",
        description="Whether log publishing search slow logs is enabled for this `AWSESDomain` node.",
    )
    log_publishing_search_slow_logs_arn: PropertyRef = PropertyRef(
        "LogPublishingSearchSlowLogsArn",
        description="ARN of the log publishing search slow logs linked to this `AWSESDomain` node.",
    )
    log_publishing_es_application_logs_enabled: PropertyRef = PropertyRef(
        "LogPublishingEsApplicationLogsEnabled",
        description="Whether log publishing elasticsearch application logs is enabled for this `AWSESDomain` node.",
    )
    log_publishing_es_application_logs_arn: PropertyRef = PropertyRef(
        "LogPublishingEsApplicationLogsArn",
        description="ARN of the log publishing Elasticsearch application logs linked to this `AWSESDomain` node.",
    )
    log_publishing_audit_logs_enabled: PropertyRef = PropertyRef(
        "LogPublishingAuditLogsEnabled",
        description="Whether log publishing audit logs is enabled for this `AWSESDomain` node.",
    )
    log_publishing_audit_logs_arn: PropertyRef = PropertyRef(
        "LogPublishingAuditLogsArn",
        description="ARN of the log publishing audit logs linked to this `AWSESDomain` node.",
    )


@dataclass(frozen=True)
class ESDomainToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ESDomainToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSESDomain`."

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
    "Represents a `PART_OF_SUBNET` relationship from `AWSESDomain` to `AWSEC2Subnet`."

    target_node_label: str = "AWSEC2Subnet"
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
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSESDomain` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSEC2SecurityGroup"
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

    label: str = "AWSESDomain"
    properties: ESDomainNodeProperties = ESDomainNodeProperties()
    sub_resource_relationship: ESDomainToAWSAccountRel = ESDomainToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ESDomainToEC2SubnetRel(),
            ESDomainToEC2SecurityGroupRel(),
        ],
    )
    # DEPRECATED: legacy ESDomain node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["ESDomain", "Database"])
