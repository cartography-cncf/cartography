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
class RDSInstanceNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DBInstanceArn")
    arn: PropertyRef = PropertyRef("DBInstanceArn", extra_index=True)
    db_instance_identifier: PropertyRef = PropertyRef(
        "DBInstanceIdentifier", extra_index=True
    )
    db_instance_class: PropertyRef = PropertyRef("DBInstanceClass")
    engine: PropertyRef = PropertyRef("Engine")
    master_username: PropertyRef = PropertyRef("MasterUsername")
    db_name: PropertyRef = PropertyRef("DBName")
    instance_create_time: PropertyRef = PropertyRef("InstanceCreateTime")
    availability_zone: PropertyRef = PropertyRef("AvailabilityZone")
    multi_az: PropertyRef = PropertyRef("MultiAZ")
    engine_version: PropertyRef = PropertyRef("EngineVersion")
    publicly_accessible: PropertyRef = PropertyRef("PubliclyAccessible")
    db_cluster_identifier: PropertyRef = PropertyRef("DBClusterIdentifier")
    storage_encrypted: PropertyRef = PropertyRef("StorageEncrypted")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    dbi_resource_id: PropertyRef = PropertyRef("DbiResourceId")
    ca_certificate_identifier: PropertyRef = PropertyRef("CACertificateIdentifier")
    enhanced_monitoring_resource_arn: PropertyRef = PropertyRef(
        "EnhancedMonitoringResourceArn"
    )
    monitoring_role_arn: PropertyRef = PropertyRef("MonitoringRoleArn")
    performance_insights_enabled: PropertyRef = PropertyRef(
        "PerformanceInsightsEnabled"
    )
    performance_insights_kms_key_id: PropertyRef = PropertyRef(
        "PerformanceInsightsKMSKeyId"
    )
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    deletion_protection: PropertyRef = PropertyRef("DeletionProtection")
    preferred_backup_window: PropertyRef = PropertyRef("PreferredBackupWindow")
    latest_restorable_time: PropertyRef = PropertyRef("LatestRestorableTime")
    preferred_maintenance_window: PropertyRef = PropertyRef(
        "PreferredMaintenanceWindow"
    )
    backup_retention_period: PropertyRef = PropertyRef("BackupRetentionPeriod")
    endpoint_address: PropertyRef = PropertyRef("EndpointAddress")
    endpoint_hostedzoneid: PropertyRef = PropertyRef("EndpointHostedZoneId")
    endpoint_port: PropertyRef = PropertyRef("EndpointPort")
    iam_database_authentication_enabled: PropertyRef = PropertyRef(
        "IAMDatabaseAuthenticationEnabled"
    )
    auto_minor_version_upgrade: PropertyRef = PropertyRef("AutoMinorVersionUpgrade")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSInstanceToAWSAccountRel(CartographyRelSchema):
    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("AWS_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RDSInstanceToAWSAccountRelProperties = (
        RDSInstanceToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RDSInstanceToEC2SecurityGroupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSInstanceToEC2SecurityGroupRel(CartographyRelSchema):
    target_node_label: str = "EC2SecurityGroup"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("security_group_ids", one_to_many=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "MEMBER_OF_EC2_SECURITY_GROUP"
    properties: RDSInstanceToEC2SecurityGroupRelProperties = (
        RDSInstanceToEC2SecurityGroupRelProperties()
    )


@dataclass(frozen=True)
class RDSInstanceToRDSInstanceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSInstanceToRDSInstanceRel(CartographyRelSchema):
    target_node_label: str = "RDSInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_instance_identifier": PropertyRef("read_replica_source_identifier"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_READ_REPLICA_OF"
    properties: RDSInstanceToRDSInstanceRelProperties = (
        RDSInstanceToRDSInstanceRelProperties()
    )


@dataclass(frozen=True)
class RDSInstanceToRDSClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSInstanceToRDSClusterRel(CartographyRelSchema):
    target_node_label: str = "RDSCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "db_cluster_identifier": PropertyRef("db_cluster_identifier"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "IS_CLUSTER_MEMBER_OF"
    properties: RDSInstanceToRDSClusterRelProperties = (
        RDSInstanceToRDSClusterRelProperties()
    )


@dataclass(frozen=True)
class RDSInstanceSchema(CartographyNodeSchema):
    label: str = "RDSInstance"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: RDSInstanceNodeProperties = RDSInstanceNodeProperties()
    sub_resource_relationship: RDSInstanceToAWSAccountRel = RDSInstanceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RDSInstanceToEC2SecurityGroupRel(),
            RDSInstanceToRDSInstanceRel(),
            RDSInstanceToRDSClusterRel(),
        ]
    )
