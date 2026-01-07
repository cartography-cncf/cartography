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
    id: PropertyRef = PropertyRef("id")
    enabled: PropertyRef = PropertyRef("enabled")
    start_time: PropertyRef = PropertyRef("start_time")
    location: PropertyRef = PropertyRef("location")
    point_in_time_recovery_enabled: PropertyRef = PropertyRef(
        "point_in_time_recovery_enabled"
    )
    transaction_log_retention_days: PropertyRef = PropertyRef(
        "transaction_log_retention_days"
    )
    backup_retention_settings: PropertyRef = PropertyRef("backup_retention_settings")
    binary_log_enabled: PropertyRef = PropertyRef("binary_log_enabled")
    instance_id: PropertyRef = PropertyRef("instance_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBackupConfigRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


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
    label: str = "GCPCloudSQLBackupConfiguration"
    properties: GCPSqlBackupConfigProperties = GCPSqlBackupConfigProperties()
    sub_resource_relationship: ProjectToBackupConfigRel = ProjectToBackupConfigRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            InstanceToBackupConfigRel(),
        ],
    )
