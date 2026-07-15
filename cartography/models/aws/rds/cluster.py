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
class RDSClusterNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("DBClusterArn", description="Same as ARN")
    arn: PropertyRef = PropertyRef(
        "DBClusterArn",
        extra_index=True,
        description="The Amazon Resource Name (ARN) for the DB cluster.",
    )
    allocated_storage: PropertyRef = PropertyRef(
        "AllocatedStorage",
        description="For all database engines except Amazon Aurora, AllocatedStorage specifies the allocated storage size in gibibytes (GiB). For Aurora, AllocatedStorage always returns 1, because Aurora DB cluster storage size isn't fixed, but instead automatically adjusts as needed.",
    )
    availability_zones: PropertyRef = PropertyRef(
        "AvailabilityZones",
        description="Provides the list of Availability Zones (AZs) where instances in the DB cluster can be created.",
    )
    backup_retention_period: PropertyRef = PropertyRef(
        "BackupRetentionPeriod",
        description="Specifies the number of days for which automatic DB snapshots are retained.",
    )
    character_set_name: PropertyRef = PropertyRef(
        "CharacterSetName",
        description="If present, specifies the name of the character set that this cluster is associated with.",
    )
    database_name: PropertyRef = PropertyRef(
        "DatabaseName",
        description="Contains the name of the initial database of this DB cluster that was provided at create time, if one was specified when the DB cluster was created. This same name is returned for the life of the DB cluster.",
    )
    db_cluster_identifier: PropertyRef = PropertyRef(
        "DBClusterIdentifier",
        extra_index=True,
        description="Contains a user-supplied DB cluster identifier. This identifier is the unique key that identifies a DB cluster.",
    )
    db_parameter_group: PropertyRef = PropertyRef(
        "DBClusterParameterGroup",
        description="Specifies the name of the DB cluster parameter group for the DB cluster.",
    )
    status: PropertyRef = PropertyRef(
        "Status", description="Specifies the current state of this DB cluster."
    )
    earliest_restorable_time: PropertyRef = PropertyRef(
        "EarliestRestorableTime",
        description="The earliest time to which a database can be restored with point-in-time restore.",
    )
    endpoint: PropertyRef = PropertyRef(
        "Endpoint",
        description="Specifies the connection endpoint for the primary instance of the DB cluster.",
    )
    reader_endpoint: PropertyRef = PropertyRef(
        "ReaderEndpoint",
        description="The reader endpoint for the DB cluster. The reader endpoint for a DB cluster load-balances connections across the Aurora Replicas that are available in a DB cluster. As clients request new connections to the reader endpoint, Aurora distributes the connection requests among the Aurora Replicas in the DB cluster. This functionality can help balance your read workload across multiple Aurora Replicas in your DB cluster. If a failover occurs, and the Aurora Replica that you are connected to is promoted to be the primary instance, your connection is dropped. To continue sending your read workload to other Aurora Replicas in the cluster, you can then reconnect to the reader endpoint.",
    )
    multi_az: PropertyRef = PropertyRef(
        "MultiAZ",
        description="Specifies whether the DB cluster has instances in multiple Availability Zones.",
    )
    engine: PropertyRef = PropertyRef(
        "Engine",
        description="The name of the database engine to be used for this DB cluster.",
    )
    engine_version: PropertyRef = PropertyRef(
        "EngineVersion", description="Indicates the database engine version."
    )
    engine_mode: PropertyRef = PropertyRef(
        "EngineMode",
        description="The DB engine mode of the DB cluster, either provisioned, serverless, parallelquery, global, or multimaster.",
    )
    latest_restorable_time: PropertyRef = PropertyRef(
        "LatestRestorableTime",
        description="Specifies the latest time to which a database can be restored with point-in-time restore.",
    )
    port: PropertyRef = PropertyRef(
        "Port",
        description="Specifies the port that the database engine is listening on.",
    )
    master_username: PropertyRef = PropertyRef(
        "MasterUsername", description="Contains the master username for the DB cluster."
    )
    preferred_backup_window: PropertyRef = PropertyRef(
        "PreferredBackupWindow",
        description="Specifies the daily time range during which automated backups are created if automated backups are enabled, as determined by the BackupRetentionPeriod.",
    )
    preferred_maintenance_window: PropertyRef = PropertyRef(
        "PreferredMaintenanceWindow",
        description="Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).",
    )
    hosted_zone_id: PropertyRef = PropertyRef(
        "HostedZoneId",
        description="Specifies the ID that Amazon Route 53 assigns when you create a hosted zone.",
    )
    storage_encrypted: PropertyRef = PropertyRef(
        "StorageEncrypted", description="Specifies whether the DB cluster is encrypted."
    )
    kms_key_id: PropertyRef = PropertyRef(
        "KmsKeyId",
        description="If StorageEncrypted is enabled, the AWS KMS key identifier for the encrypted DB cluster. The AWS KMS key identifier is the key ARN, key ID, alias ARN, or alias name for the AWS KMS customer master key (CMK).",
    )
    db_cluster_resource_id: PropertyRef = PropertyRef(
        "DbClusterResourceId",
        description="The AWS Region-unique, immutable identifier for the DB cluster. This identifier is found in AWS CloudTrail log entries whenever the AWS KMS CMK for the DB cluster is accessed.",
    )
    clone_group_id: PropertyRef = PropertyRef(
        "CloneGroupId",
        description="Identifies the clone group to which the DB cluster is associated.",
    )
    cluster_create_time: PropertyRef = PropertyRef(
        "ClusterCreateTime",
        description="Specifies the time when the DB cluster was created, in Universal Coordinated Time (UTC).",
    )
    earliest_backtrack_time: PropertyRef = PropertyRef(
        "EarliestBacktrackTime",
        description="The earliest time to which a DB cluster can be backtracked.",
    )
    backtrack_window: PropertyRef = PropertyRef(
        "BacktrackWindow",
        description="The target backtrack window, in seconds. If this value is set to 0, backtracking is disabled for the DB cluster. Otherwise, backtracking is enabled.",
    )
    backtrack_consumed_change_records: PropertyRef = PropertyRef(
        "BacktrackConsumedChangeRecords",
        description="The number of change records stored for Backtrack.",
    )
    capacity: PropertyRef = PropertyRef(
        "Capacity",
        description="The current capacity of an Aurora Serverless DB cluster. The capacity is 0 (zero) when the cluster is paused.",
    )
    scaling_configuration_info_min_capacity: PropertyRef = PropertyRef(
        "ScalingConfigurationInfoMinCapacity",
        description="The minimum capacity for the Aurora DB cluster in serverless DB engine mode.",
    )
    scaling_configuration_info_max_capacity: PropertyRef = PropertyRef(
        "ScalingConfigurationInfoMaxCapacity",
        description="The maximum capacity for an Aurora DB cluster in serverless DB engine mode.",
    )
    scaling_configuration_info_auto_pause: PropertyRef = PropertyRef(
        "ScalingConfigurationInfoAutoPause",
        description="A value that indicates whether automatic pause is allowed for the Aurora DB cluster in serverless DB engine mode.",
    )
    deletion_protection: PropertyRef = PropertyRef(
        "DeletionProtection",
        description="Indicates if the DB cluster has deletion protection enabled. The database can't be deleted when deletion protection is enabled.",
    )
    region: PropertyRef = PropertyRef(
        "Region",
        set_in_kwargs=True,
        description="AWS Region containing this `AWSRDSCluster` node.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated",
    )


@dataclass(frozen=True)
class RDSClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSClusterToAWSAccountRel(CartographyRelSchema):
    "Represents a `RESOURCE` relationship from `AWSAccount` to `AWSRDSCluster`."

    target_node_label: str = "AWSAccount"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("AWS_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: RDSClusterToAWSAccountRelProperties = (
        RDSClusterToAWSAccountRelProperties()
    )


@dataclass(frozen=True)
class RDSClusterSchema(CartographyNodeSchema):
    "Represents an `AWSRDSCluster` node in the AWS graph."

    label: str = "AWSRDSCluster"
    # DEPRECATED: legacy RDSCluster node label will be removed in v1.0.0.
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["RDSCluster"])
    properties: RDSClusterNodeProperties = RDSClusterNodeProperties()
    sub_resource_relationship: RDSClusterToAWSAccountRel = RDSClusterToAWSAccountRel()
