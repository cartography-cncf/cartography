import cartography.intel.gcp.storage
import tests.data.gcp.storage
from tests.integration.util import check_nodes
from tests.integration.util import check_rels
from unittest.mock import patch

OLD_UPDATE_TAG = 12345
NEW_UPDATE_TAG = 67890
TEST_PROJECT_ID = 9999

def _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session):
    """
    Populate graph with fake GCP Storage Bucket data and a related GCPProject node.
    """
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectId})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $UpdateTag, p.projectnumber = $ProjectId
        """,
        ProjectId=TEST_PROJECT_ID,
        UpdateTag=OLD_UPDATE_TAG, 
    )

    bucket_res = tests.data.gcp.storage.STORAGE_RESPONSE['items']
    bucket_list = cartography.intel.gcp.storage.transform_gcp_buckets(bucket_res)
    cartography.intel.gcp.storage.load_gcp_buckets(
        neo4j_session,
        bucket_list,
        TEST_PROJECT_ID,
        OLD_UPDATE_TAG, 
    )

def test_transform_and_load_storage_buckets(neo4j_session):
    """
    Test that we can correctly transform and load GCP Storage Buckets to Neo4j.
    """
    _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session)

    expected_nodes = {
        ("bucket_name", TEST_PROJECT_ID, "storage#bucket"),
    }
    actual_nodes = check_nodes(
        neo4j_session,
        "GCPBucket",
        ["id", "project_number", "kind"],
    )
    assert actual_nodes == expected_nodes

    expected_rels = {
        (TEST_PROJECT_ID, "bucket_name"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBucket",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels

def test_attach_storage_bucket_labels(neo4j_session):
    """
    Test that we can attach GCP storage bucket labels.
    """
    
    _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session)

    expected_rels = {
        ("bucket_name", "bucket_name_label_key_1"),
        ("bucket_name", "bucket_name_label_key_2"),
    }
    actual_rels = check_rels(
        neo4j_session,
        "GCPBucket",
        "id",
        "GCPBucketLabel",
        "id",
        "LABELED",
        rel_direction_right=True,
    )
    assert actual_rels == expected_rels

    expected_label_nodes = {
        ("bucket_name_label_key_1", "label_key_1", "label_value_1"),
        ("bucket_name_label_key_2", "label_key_2", "label_value_2"),
    }
    actual_label_nodes = check_nodes(
        neo4j_session,
        "GCPBucketLabel",
        ["id", "key", "value"],
    )
    assert actual_label_nodes == expected_label_nodes

@patch('cartography.intel.gcp.storage.get_gcp_buckets')
def test_sync_removes_stale_buckets_and_labels(mock_get, neo4j_session):
    """
    Test that the sync function correctly removes stale buckets and their labels.
    """
    _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session)

    assert check_nodes(neo4j_session, "GCPBucket", ["id"])
    assert check_nodes(neo4j_session, "GCPBucketLabel", ["id"])

    mock_get.return_value = []
    cartography.intel.gcp.storage.sync_gcp_buckets(
        neo4j_session,
        None,
        TEST_PROJECT_ID,
        NEW_UPDATE_TAG, 
        {"UPDATE_TAG": NEW_UPDATE_TAG}, 
    )

    assert not check_nodes(neo4j_session, "GCPBucket", ["id"])
    assert not check_nodes(neo4j_session, "GCPBucketLabel", ["id"])