import logging
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

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GCPSqlBackupConfigProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthetic `{instance_self_link}/backupConfig` identifier.",
    )
    enabled: PropertyRef = PropertyRef(
        "enabled",
        description="Boolean indicating whether automated backups are enabled.",
    )
    start_time: PropertyRef = PropertyRef(
        "start_time",
        description="Configured backup window start time or operation start timestamp.",
    )
    location: PropertyRef = PropertyRef(
        "location", description="The location where backups are stored."
    )
    point_in_time_recovery_enabled: PropertyRef = PropertyRef(
        "point_in_time_recovery_enabled",
        description="Whether Cloud SQL point-in-time recovery is enabled.",
    )
    transaction_log_retention_days: PropertyRef = PropertyRef(
        "transaction_log_retention_days",
        description="Number of days Cloud SQL retains transaction logs for point-in-time recovery.",
    )
    backup_retention_settings: PropertyRef = PropertyRef(
        "backup_retention_settings",
        description="Cloud SQL retained-backup configuration encoded as JSON.",
    )
    binary_log_enabled: PropertyRef = PropertyRef(
        "binary_log_enabled",
        description="Whether MySQL binary logging is enabled for recovery and replication.",
    )
    instance_id: PropertyRef = PropertyRef(
        "instance_id",
        description="Identifier of the parent service instance.",
    )
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last time the node was updated.",
    )


@dataclass(frozen=True)
class ProjectToBackupConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class ProjectToBackupConfigRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToBackupConfigRelProperties = (
        ProjectToBackupConfigRelProperties()
    )


@dataclass(frozen=True)
class InstanceToBackupConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef(
        "lastupdated",
        set_in_kwargs=True,
        description="Timestamp of the last sync that observed this data.",
    )


@dataclass(frozen=True)
class InstanceToBackupConfigRel(CartographyRelSchema):
    target_node_label: str = "GCPCloudSQLInstance"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("instance_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "HAS_BACKUP_CONFIG"
    properties: InstanceToBackupConfigRelProperties = (
        InstanceToBackupConfigRelProperties()
    )


@dataclass(frozen=True)
class GCPSqlBackupConfigSchema(CartographyNodeSchema):
    """Representation of a GCP [Cloud SQL Backup Configuration](https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/instances#backupconfiguration). This node captures the backup settings for a Cloud SQL instance."""

    label: str = "GCPCloudSQLBackupConfiguration"
    properties: GCPSqlBackupConfigProperties = GCPSqlBackupConfigProperties()
    sub_resource_relationship: ProjectToBackupConfigRel = ProjectToBackupConfigRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InstanceToBackupConfigRel(),
        ],
    )
