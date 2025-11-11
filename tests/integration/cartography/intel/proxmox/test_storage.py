"""
Integration tests for Proxmox storage module.
"""

from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.proxmox.storage
from cartography.intel.proxmox.storage import sync as storage_sync
from tests.data.proxmox.compute import MOCK_STORAGE_DATA
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_CLUSTER_ID = "test-cluster"


@patch.object(
    cartography.intel.proxmox.storage, "get_storage", return_value=MOCK_STORAGE_DATA
)
def test_sync_storage(mock_get_storage, neo4j_session):
    """
    Test that storage backends sync correctly.
    """
    # Arrange - Create cluster node first (required for relationships)
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    storage_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check storage nodes
    expected_storage_nodes = {
        ("local", "local", "dir", False),
        ("local-lvm", "local-lvm", "lvmthin", False),
        ("nfs-backup", "nfs-backup", "nfs", True),
    }
    assert (
        check_nodes(neo4j_session, "ProxmoxStorage", ["id", "name", "type", "shared"])
        == expected_storage_nodes
    )

    # Assert - Check storage->cluster relationships
    expected_rels = {
        ("local", TEST_CLUSTER_ID),
        ("local-lvm", TEST_CLUSTER_ID),
        ("nfs-backup", TEST_CLUSTER_ID),
    }
    assert (
        check_rels(
            neo4j_session,
            "ProxmoxStorage",
            "id",
            "ProxmoxCluster",
            "id",
            "RESOURCE",
            rel_direction_right=True,
        )
        == expected_rels
    )


@patch.object(
    cartography.intel.proxmox.storage, "get_storage", return_value=MOCK_STORAGE_DATA
)
def test_storage_properties(mock_get_storage, neo4j_session):
    """
    Test that storage properties are correctly stored.
    """
    # Arrange - Create cluster node first (required for relationships)
    neo4j_session.run(
        """
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        SET c.name = $cluster_id
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    storage_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check local storage properties
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxStorage {id: 'local'})
        RETURN s.name, s.type, s.content_types, s.shared, s.enabled
        """
    )
    data = result.single()
    assert data is not None
    assert data["s.name"] == "local"
    assert data["s.type"] == "dir"
    # content_types is stored as a list, not a string
    assert "backup" in data["s.content_types"]
    assert "iso" in data["s.content_types"]
    assert data["s.shared"] is False
    assert data["s.enabled"] is True
    # Note: available/total/used require storage status from nodes, not tested here

    # Assert - Check NFS storage properties
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxStorage {id: 'nfs-backup'})
        RETURN s.name, s.type, s.shared
        """
    )
    data = result.single()
    assert data is not None
    assert data["s.name"] == "nfs-backup"
    assert data["s.type"] == "nfs"
    assert data["s.shared"] is True
    # Note: NFS-specific fields like server/export are not currently captured in the model


@patch.object(
    cartography.intel.proxmox.storage, "get_storage", return_value=MOCK_STORAGE_DATA
)
def test_storage_node_relationships(mock_get_storage, neo4j_session):
    """
    Test that storage to node AVAILABLE_ON relationships are created.
    """
    # First, create some mock nodes so we have something to relate to
    neo4j_session.run(
        """
        MERGE (n1:ProxmoxNode {id: 'node1', name: 'node1'})
        MERGE (n2:ProxmoxNode {id: 'node2', name: 'node2'})
        MERGE (c:ProxmoxCluster {id: $cluster_id})
        """,
        cluster_id=TEST_CLUSTER_ID,
    )

    # Arrange
    proxmox = MagicMock()
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "CLUSTER_ID": TEST_CLUSTER_ID,
    }

    # Act
    storage_sync(
        neo4j_session,
        proxmox,
        TEST_CLUSTER_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check storage->node AVAILABLE_ON relationships
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxStorage {id: 'local'})-[r:AVAILABLE_ON]->(n:ProxmoxNode)
        RETURN n.name
        ORDER BY n.name
        """
    )
    nodes = [record["n.name"] for record in result]
    assert nodes == ["node1", "node2"]

    # Assert - Check shared storage is available on all nodes
    result = neo4j_session.run(
        """
        MATCH (s:ProxmoxStorage {id: 'nfs-backup'})-[r:AVAILABLE_ON]->(n:ProxmoxNode)
        RETURN n.name
        ORDER BY n.name
        """
    )
    nodes = [record["n.name"] for record in result]
    assert nodes == ["node1", "node2"]
