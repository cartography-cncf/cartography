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
    id: PropertyRef = PropertyRef("DBInstanceArn", description="Same as ARN")
    arn: PropertyRef = PropertyRef(
        "DBInstanceArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the DB instance.",
    )
    db_instance_identifier: PropertyRef = PropertyRef(
        "DBInstanceIdentifier",
        extra_index=True,
        description="Contains a user-supplied database identifier. This identifier is the unique key that identifies a DB instance.",
    )
    db_instance_class: PropertyRef = PropertyRef(
        "DBInstanceClass",
        description="Contains the name of the compute and memory capacity class of the DB instance.",
    )
    engine: PropertyRef = PropertyRef(
        "Engine",
        description="Provides the name of the database engine to be used for this DB instance.",
    )
    master_username: PropertyRef = PropertyRef(
        "MasterUsername",
        description="Contains the master username for the DB instance.",
    )
    db_name: PropertyRef = PropertyRef(
        "DBName",
        description="The meaning of this parameter differs according to the database engine you use. For example, this value returns MySQL, MariaDB, or PostgreSQL information when returning values from CreateDBInstanceReadReplica since Read Replicas are only supported for these engines.<br><br>**MySQL, MariaDB, SQL Server, PostgreSQL:** Contains the name of the initial database of this instance that was provided at create time, if one was specified when the DB instance was created. This same name is returned for the life of the DB instance.<br><br>**Oracle:** Contains the Oracle System ID (SID) of the created DB instance. Not shown when the returned parameters do not apply to an Oracle DB instance.",
    )
    instance_create_time: PropertyRef = PropertyRef(
        "InstanceCreateTime",
        description="Provides the date and time the DB instance was created.",
    )
    availability_zone: PropertyRef = PropertyRef(
        "AvailabilityZone",
        description="Specifies the name of the Availability Zone the DB instance is located in.",
    )
    multi_az: PropertyRef = PropertyRef(
        "MultiAZ", description="Specifies if the DB instance is a Multi-AZ deployment."
    )
    engine_version: PropertyRef = PropertyRef(
        "EngineVersion", description="Indicates the database engine version."
    )
    publicly_accessible: PropertyRef = PropertyRef(
        "PubliclyAccessible",
        description="Specifies the accessibility options for the DB instance. A value of true specifies an Internet-facing instance with a publicly resolvable DNS name, which resolves to a public IP address. A value of false specifies an internal instance with a DNS name that resolves to a private IP address.",
    )
    db_cluster_identifier: PropertyRef = PropertyRef(
        "DBClusterIdentifier",
        description="If the DB instance is a member of a DB cluster, contains the name of the DB cluster that the DB instance is a member of.",
    )
    storage_encrypted: PropertyRef = PropertyRef(
        "StorageEncrypted",
        description="Specifies whether the DB instance is encrypted.",
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="If StorageEncrypted is true, the AWS KMS key identifier for the encrypted DB instance.",
    )
    dbi_resource_id: PropertyRef = PropertyRef(
        "DbiResourceId",
        description="The AWS Region-unique, immutable identifier for the DB instance. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS key for the DB instance is accessed.",
    )
    ca_certificate_identifier: PropertyRef = PropertyRef(
        "CACertificateIdentifier",
        description="The identifier of the CA certificate for this DB instance.",
    )
    enhanced_monitoring_resource_arn: PropertyRef = PropertyRef(
        "EnhancedMonitoringResourceArn",
        description="The Amazon Resource Name (ARN) of the Amazon CloudWatch Logs log stream that receives the Enhanced Monitoring metrics data for the DB instance.",
    )
    monitoring_role_arn: PropertyRef = PropertyRef(
        "MonitoringRoleArn",
        description="The ARN for the IAM role that permits RDS to send Enhanced Monitoring metrics to Amazon CloudWatch Logs.",
    )
    performance_insights_enabled: PropertyRef = PropertyRef(
        "PerformanceInsightsEnabled",
        description="True if Performance Insights is enabled for the DB instance, and otherwise false.",
    )
    performance_insights_kms_key_id: PropertyRef = PropertyRef(
        "PerformanceInsightsKMSKeyId",
        description="Identifier of the performance insights KMS key linked to this `AWSRDSInstance` node.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSRDSInstance` node.",
    )
    deletion_protection: PropertyRef = PropertyRef(
        "DeletionProtection",
        description="Whether deletion protection is enabled for the DB instance.",
    )
    preferred_backup_window: PropertyRef = PropertyRef(
        "PreferredBackupWindow",
        description="Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod.",
    )
    latest_restorable_time: PropertyRef = PropertyRef(
        "LatestRestorableTime",
        description="Latest timestamp to which the DB instance can be restored.",
    )
    preferred_maintenance_window: PropertyRef = PropertyRef(
        "PreferredMaintenanceWindow",
        description="Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).",
    )
    backup_retention_period: PropertyRef = PropertyRef(
        "BackupRetentionPeriod",
        description="Specifies the number of days for which automatic DB snapshots are retained.",
    )
    endpoint_address: PropertyRef = PropertyRef(
        "EndpointAddress", description="DNS name of the RDS instance"
    )
    endpoint_hostedzoneid: PropertyRef = PropertyRef(
        "EndpointHostedZoneId",
        description="The AWS DNS Zone ID that is associated with the RDS instance's DNS entry",
    )
    endpoint_port: PropertyRef = PropertyRef(
        "EndpointPort", description="The port that the RDS instance is listening on"
    )
    iam_database_authentication_enabled: PropertyRef = PropertyRef(
        "IAMDatabaseAuthenticationEnabled",
        description="Specifies if mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled",
    )
    auto_minor_version_upgrade: PropertyRef = PropertyRef(
        "AutoMinorVersionUpgrade",
        description="Specifies whether minor version upgrades are applied automatically to the DB instance during the maintenance window",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class RDSInstanceToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSInstanceToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSRDSInstance`."

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
    "Represents a `MEMBER_OF_EC2_SECURITY_GROUP` relationship from `AWSRDSInstance` to `AWSEC2SecurityGroup`."

    target_node_label: str = "AWSEC2SecurityGroup"
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
    "Represents a `IS_READ_REPLICA_OF` relationship from `AWSRDSInstance` to `AWSRDSInstance`."

    target_node_label: str = "AWSRDSInstance"
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
    "Represents a `IS_CLUSTER_MEMBER_OF` relationship from `AWSRDSInstance` to `AWSRDSCluster`."

    target_node_label: str = "AWSRDSCluster"
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
class RDSInstanceToKMSKeyRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# Canonical ontology edge: (:Database)-[:ENCRYPTED_BY]->(:EncryptionKey).
# Only created when the instance has a customer-managed KMS key (KmsKeyId is the
# key ARN).
class RDSInstanceToKMSKeyRel(CartographyRelSchema):
    "Represents a `ENCRYPTED_BY` relationship from `AWSRDSInstance` to `AWSKMSKey`."

    target_node_label: str = "AWSKMSKey"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"arn": PropertyRef("KmsKeyId")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "ENCRYPTED_BY"
    properties: RDSInstanceToKMSKeyRelProperties = RDSInstanceToKMSKeyRelProperties()


@dataclass(frozen=True)
class RDSInstanceSchema(CartographyNodeSchema):
    "Represents an `AWSRDSInstance` node in the AWS graph."

    label: str = "AWSRDSInstance"
    # DEPRECATED: legacy RDSInstance node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["RDSInstance", "Database"])
    properties: RDSInstanceNodeProperties = RDSInstanceNodeProperties()
    sub_resource_relationship: RDSInstanceToAWSAccountRel = RDSInstanceToAWSAccountRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            RDSInstanceToEC2SecurityGroupRel(),
            RDSInstanceToRDSInstanceRel(),
            RDSInstanceToRDSClusterRel(),
            RDSInstanceToKMSKeyRel(),
        ]
    )
