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
class GCPBigtableBackupProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("name")
    name: PropertyRef = PropertyRef("name")
    source_table: PropertyRef = PropertyRef("sourceTable")
    expire_time: PropertyRef = PropertyRef("expireTime")
    start_time: PropertyRef = PropertyRef("startTime")
    end_time: PropertyRef = PropertyRef("endTime")
    size_bytes: PropertyRef = PropertyRef("sizeBytes")
    state: PropertyRef = PropertyRef("state")
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableBackupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProjectToBigtableBackupRel(CartographyRelSchema):
    target_node_label: str = "GCPProject"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("PROJECT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: ProjectToBigtableBackupRelProperties = (
        ProjectToBigtableBackupRelProperties()
    )


@dataclass(frozen=True)
class BackupToClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BackupToClusterRel(CartographyRelSchema):
    target_node_label: str = "GCPBigtableCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("cluster_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "STORES_BACKUP"
    properties: BackupToClusterRelProperties = BackupToClusterRelProperties()


@dataclass(frozen=True)
class TableToBackupRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class TableToBackupRel(CartographyRelSchema):
    target_node_label: str = "GCPBigtableTable"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("source_table")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "BACKED_UP_AS"
    properties: TableToBackupRelProperties = TableToBackupRelProperties()


@dataclass(frozen=True)
class GCPBigtableBackupSchema(CartographyNodeSchema):
    label: str = "GCPBigtableBackup"
    properties: GCPBigtableBackupProperties = GCPBigtableBackupProperties()
    sub_resource_relationship: ProjectToBigtableBackupRel = ProjectToBigtableBackupRel()
    other_relationships: OtherRelationships = OtherRelationships(
        [
            BackupToClusterRel(),
            TableToBackupRel(),
        ],
    )
