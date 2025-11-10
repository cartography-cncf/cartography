"""
Data models for Proxmox backup jobs.

Follows Cartography's modern data model pattern.
"""

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

# ============================================================================
# ProxmoxBackupJob Node Schema
# ============================================================================


@dataclass(frozen=True)
class ProxmoxBackupJobNodeProperties(CartographyNodeProperties):
    """
    Properties for a ProxmoxBackupJob node.

    Represents scheduled backup configurations in Proxmox.
    """

    id: PropertyRef = PropertyRef("id")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    job_id: PropertyRef = PropertyRef("job_id", extra_index=True)
    cluster_id: PropertyRef = PropertyRef("cluster_id")
    schedule: PropertyRef = PropertyRef("schedule")  # Cron-style schedule
    storage: PropertyRef = PropertyRef("storage")  # Target storage for backups
    enabled: PropertyRef = PropertyRef("enabled")
    mode: PropertyRef = PropertyRef("mode")  # snapshot, suspend, stop
    compression: PropertyRef = PropertyRef("compression")  # zstd, gzip, lzo, none
    mailnotification: PropertyRef = PropertyRef("mailnotification")
    mailto: PropertyRef = PropertyRef("mailto")
    notes: PropertyRef = PropertyRef("notes")
    # Flattened retention (prune-backups) settings. Each is optional and may be None.
    prune_keep_last: PropertyRef = PropertyRef("prune_keep_last")
    prune_keep_hourly: PropertyRef = PropertyRef("prune_keep_hourly")
    prune_keep_daily: PropertyRef = PropertyRef("prune_keep_daily")
    prune_keep_weekly: PropertyRef = PropertyRef("prune_keep_weekly")
    prune_keep_monthly: PropertyRef = PropertyRef("prune_keep_monthly")
    prune_keep_yearly: PropertyRef = PropertyRef("prune_keep_yearly")
    repeat_missed: PropertyRef = PropertyRef("repeat_missed")


@dataclass(frozen=True)
class ProxmoxBackupJobToClusterRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxBackupJob to ProxmoxCluster.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxBackupJobToClusterRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxBackupJob)-[:RESOURCE]->(:ProxmoxCluster)

    Backup jobs belong to clusters.
    """

    target_node_label: str = "ProxmoxCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("CLUSTER_ID", set_in_kwargs=True),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "RESOURCE"
    properties: ProxmoxBackupJobToClusterRelProperties = (
        ProxmoxBackupJobToClusterRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxBackupJobToStorageRelProperties(CartographyRelProperties):
    """
    Properties for relationship from ProxmoxBackupJob to ProxmoxStorage.
    """

    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class ProxmoxBackupJobToStorageRel(CartographyRelSchema):
    """
    Relationship: (:ProxmoxBackupJob)-[:BACKS_UP_TO]->(:ProxmoxStorage)

    Backup jobs target storage backends.
    """

    target_node_label: str = "ProxmoxStorage"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "id": PropertyRef("storage"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "BACKS_UP_TO"
    properties: ProxmoxBackupJobToStorageRelProperties = (
        ProxmoxBackupJobToStorageRelProperties()
    )


@dataclass(frozen=True)
class ProxmoxBackupJobSchema(CartographyNodeSchema):
    """
    Schema for ProxmoxBackupJob.

    Backup jobs define scheduled VM/container backup configurations.
    """

    label: str = "ProxmoxBackupJob"
    properties: ProxmoxBackupJobNodeProperties = ProxmoxBackupJobNodeProperties()
    sub_resource_relationship: ProxmoxBackupJobToClusterRel = (
        ProxmoxBackupJobToClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            ProxmoxBackupJobToStorageRel(),
        ]
    )
