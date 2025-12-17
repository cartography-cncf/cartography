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
    id: PropertyRef = PropertyRef("DBClusterArn")
    arn: PropertyRef = PropertyRef("DBClusterArn", extra_index=True)
    allocated_storage: PropertyRef = PropertyRef("AllocatedStorage")
    availability_zones: PropertyRef = PropertyRef("AvailabilityZones")
    backup_retention_period: PropertyRef = PropertyRef("BackupRetentionPeriod")
    character_set_name: PropertyRef = PropertyRef("CharacterSetName")
    database_name: PropertyRef = PropertyRef("DatabaseName")
    db_cluster_identifier: PropertyRef = PropertyRef(
        "DBClusterIdentifier", extra_index=True
    )
    db_parameter_group: PropertyRef = PropertyRef("DBClusterParameterGroup")
    status: PropertyRef = PropertyRef("Status")
    earliest_restorable_time: PropertyRef = PropertyRef("EarliestRestorableTime")
    endpoint: PropertyRef = PropertyRef("Endpoint")
    reader_endpoint: PropertyRef = PropertyRef("ReaderEndpoint")
    multi_az: PropertyRef = PropertyRef("MultiAZ")
    engine: PropertyRef = PropertyRef("Engine")
    engine_version: PropertyRef = PropertyRef("EngineVersion")
    engine_mode: PropertyRef = PropertyRef("EngineMode")
    latest_restorable_time: PropertyRef = PropertyRef("LatestRestorableTime")
    port: PropertyRef = PropertyRef("Port")
    master_username: PropertyRef = PropertyRef("MasterUsername")
    preferred_backup_window: PropertyRef = PropertyRef("PreferredBackupWindow")
    preferred_maintenance_window: PropertyRef = PropertyRef(
        "PreferredMaintenanceWindow"
    )
    hosted_zone_id: PropertyRef = PropertyRef("HostedZoneId")
    storage_encrypted: PropertyRef = PropertyRef("StorageEncrypted")
    kms_key_id: PropertyRef = PropertyRef("KmsKeyId")
    db_cluster_resource_id: PropertyRef = PropertyRef("DbClusterResourceId")
    clone_group_id: PropertyRef = PropertyRef("CloneGroupId")
    cluster_create_time: PropertyRef = PropertyRef("ClusterCreateTime")
    earliest_backtrack_time: PropertyRef = PropertyRef("EarliestBacktrackTime")
    backtrack_window: PropertyRef = PropertyRef("BacktrackWindow")
    backtrack_consumed_change_records: PropertyRef = PropertyRef(
        "BacktrackConsumedChangeRecords"
    )
    capacity: PropertyRef = PropertyRef("Capacity")
    scaling_configuration_info_min_capacity: PropertyRef = PropertyRef(
        "ScalingConfigurationInfoMinCapacity"
    )
    scaling_configuration_info_max_capacity: PropertyRef = PropertyRef(
        "ScalingConfigurationInfoMaxCapacity"
    )
    scaling_configuration_info_auto_pause: PropertyRef = PropertyRef(
        "ScalingConfigurationInfoAutoPause"
    )
    deletion_protection: PropertyRef = PropertyRef("DeletionProtection")
    region: PropertyRef = PropertyRef("Region", set_in_kwargs=True)
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSClusterToAWSAccountRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class RDSClusterToAWSAccountRel(CartographyRelSchema):
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
    label: str = "RDSCluster"
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels(["Database"])
    properties: RDSClusterNodeProperties = RDSClusterNodeProperties()
    sub_resource_relationship: RDSClusterToAWSAccountRel = RDSClusterToAWSAccountRel()
