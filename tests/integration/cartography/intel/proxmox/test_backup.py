"""
Integration tests for Proxmox backup job sync.
"""

from typing import Any
from unittest.mock import patch

import cartography.intel.proxmox.backup
from tests.data.proxmox.backup import MOCK_BACKUP_JOB_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(
    cartography.intel.proxmox.backup,
    "get_backup_jobs",
    return_value=MOCK_BACKUP_JOB_DATA,
)
def test_sync_backup_jobs(mock_get_jobs, neo4j_session):
    """
    Test that backup jobs sync correctly and create proper nodes and relationships.
    """
    # Arrange
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster first
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id,
            c.lastupdated = $update_tag
        """,
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create storage and VMs for relationship tests
    neo4j_session.run(
        """
        MERGE (s1:ProxmoxStorage {id: 'nfs-backup'})
        SET s1.name = 'nfs-backup', s1.lastupdated = $update_tag
        MERGE (s2:ProxmoxStorage {id: 'local'})
        SET s2.name = 'local', s2.lastupdated = $update_tag
        MERGE (v1:ProxmoxVM {vmid: 100})
        SET v1.id = 'node1:100', v1.name = 'test-vm-1', v1.lastupdated = $update_tag
        MERGE (v2:ProxmoxVM {vmid: 101})
        SET v2.id = 'node1:101', v2.name = 'test-vm-2', v2.lastupdated = $update_tag
        MERGE (v3:ProxmoxVM {vmid: 200})
        SET v3.id = 'node2:200', v3.name = 'test-container-1', v3.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.proxmox.backup.sync(
        neo4j_session,
        None,  # proxmox_client mocked
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Backup jobs exist
    expected_jobs = {
        ("backup-daily-vms", "0 2 * * *", True),
        ("backup-weekly-full", "0 0 * * 0", True),
        ("backup-containers", "0 3 * * *", True),
        ("backup-disabled", "0 4 * * *", False),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxBackupJob", ["id", "schedule", "enabled"])
        == expected_jobs
    )

    # Assert - Backup job to cluster relationships
    expected_rels = {
        ("backup-daily-vms", TEST_CLUSTER_ID),
        ("backup-weekly-full", TEST_CLUSTER_ID),
        ("backup-containers", TEST_CLUSTER_ID),
        ("backup-disabled", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxBackupJob",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )

    # Assert - Backup job to storage relationships
    expected_storage_rels = {
        ("backup-daily-vms", "nfs-backup"),
        ("backup-weekly-full", "nfs-backup"),
        ("backup-containers", "local"),
        ("backup-disabled", "local"),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxBackupJob",
            "id",
            "ProxmoxStorage",
            "id",
            "BACKS_UP_TO",
            rel_direction_right=True,
        )
        == expected_storage_rels
    )

    # Assert - Backup job to VM relationships
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxBackupJob)-[:BACKS_UP]->(v:ProxmoxVM)
        RETURN j.id as job_id, v.vmid as vmid
        ORDER BY job_id, vmid
        """
    )
    job_vm_rels = [(r["job_id"], r["vmid"]) for r in result]
    # backup-daily-vms backs up VMs 100 and 101
    # backup-containers backs up container 200
    # backup-weekly-full has "all" so no specific relationships
    assert job_vm_rels == [
        ("backup-containers", 200),
        ("backup-daily-vms", 100),
        ("backup-daily-vms", 101),
    ]

    # Assert - Backup mode and compression are set correctly
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxBackupJob {id: 'backup-daily-vms'})
        RETURN j.mode as mode, j.compression as compression
        """
    )
    record = result.single()
    assert record["mode"] == "snapshot"
    assert record["compression"] == "zstd"


def test_backup_job_prune_properties(neo4j_session):
    """
    Test that prune-backups map is correctly flattened into primitive properties.
    This verifies the fix for Neo4j CypherTypeError when storing map values.
    """
    # Arrange
    common_job_parameters: dict[str, Any] = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Create cluster
    neo4j_session.run(
        "MERGE (c:ProxmoxCluster {id: $cluster_id}) SET c.lastupdated = $update_tag",
        cluster_id=TEST_CLUSTER_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    # Create storage
    neo4j_session.run(
        "MERGE (s:ProxmoxStorage {id: 'nfs-backup'}) SET s.lastupdated = $update_tag",
        update_tag=TEST_UPDATE_TAG,
    )

    # Act - sync with mocked data containing prune-backups maps
    with patch.object(
        cartography.intel.proxmox.backup,
        "get_backup_jobs",
        return_value=MOCK_BACKUP_JOB_DATA,
    ):
        cartography.intel.proxmox.backup.sync(
            neo4j_session,
            None,
            TEST_CLUSTER_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Assert - Prune properties for backup-daily-vms (has last, weekly, monthly)
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxBackupJob {id: 'backup-daily-vms'})
        RETURN j.prune_keep_last as last,
               j.prune_keep_hourly as hourly,
               j.prune_keep_daily as daily,
               j.prune_keep_weekly as weekly,
               j.prune_keep_monthly as monthly,
               j.prune_keep_yearly as yearly
        """
    )
    record = result.single()
    assert record["last"] == 7  # Should be converted to int
    assert record["hourly"] is None  # Not present in data
    assert record["daily"] is None
    assert record["weekly"] == 4
    assert record["monthly"] == 6
    assert record["yearly"] is None

    # Assert - Prune properties for backup-weekly-full (has last, hourly)
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxBackupJob {id: 'backup-weekly-full'})
        RETURN j.prune_keep_last as last,
               j.prune_keep_hourly as hourly,
               j.prune_keep_daily as daily
        """
    )
    record = result.single()
    assert record["last"] == 4
    assert record["hourly"] == 2
    assert record["daily"] is None

    # Assert - Prune properties for backup-containers (has last, daily, yearly)
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxBackupJob {id: 'backup-containers'})
        RETURN j.prune_keep_last as last,
               j.prune_keep_daily as daily,
               j.prune_keep_yearly as yearly,
               j.prune_keep_hourly as hourly
        """
    )
    record = result.single()
    assert record["last"] == 3
    assert record["daily"] == 10
    assert record["yearly"] == 2
    assert record["hourly"] is None

    # Assert - Backup job with no prune-backups should have all None values
    result = neo4j_session.run(
        """
        MATCH (j:ProxmoxBackupJob {id: 'backup-disabled'})
        RETURN j.prune_keep_last as last,
               j.prune_keep_hourly as hourly,
               j.prune_keep_daily as daily,
               j.prune_keep_weekly as weekly,
               j.prune_keep_monthly as monthly,
               j.prune_keep_yearly as yearly
        """
    )
    record = result.single()
    assert record["last"] is None
    assert record["hourly"] is None
    assert record["daily"] is None
    assert record["weekly"] is None
    assert record["monthly"] is None
    assert record["yearly"] is None
