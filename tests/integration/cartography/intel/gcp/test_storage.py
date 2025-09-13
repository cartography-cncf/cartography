from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.storage
import tests.data.gcp.storage
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session):
    # Create test project first
    _create_test_project(neo4j_session)

    bucket_res = tests.data.gcp.storage.STORAGE_RESPONSE
    buckets, bucket_labels = (
        cartography.intel.gcp.storage.transform_gcp_buckets_and_labels(bucket_res)
    )
    cartography.intel.gcp.storage.load_gcp_buckets(
        neo4j_session,
        buckets,
        "project-abc",  # project_id parameter
        TEST_UPDATE_TAG,
    )
    cartography.intel.gcp.storage.load_gcp_bucket_labels(
        neo4j_session,
        bucket_labels,
        "project-abc",  # project_id parameter
        TEST_UPDATE_TAG,
    )


def test_transform_and_load_storage_buckets(neo4j_session):
    """
    Test that we can correctly transform and load GCP Storage Buckets to Neo4j.
    """
    _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session)
    query = """
    MATCH(bucket:GCPBucket{id:$BucketId})
    RETURN bucket.id, bucket.project_number, bucket.kind
    """
    expected_id = "bucket_name"
    expected_project_num = 9999
    expected_kind = "storage#bucket"
    nodes = neo4j_session.run(
        query,
        BucketId=expected_id,
    )
    actual_nodes = {
        (n["bucket.id"], n["bucket.project_number"], n["bucket.kind"]) for n in nodes
    }
    expected_nodes = {
        (expected_id, expected_project_num, expected_kind),
    }
    assert actual_nodes == expected_nodes


def test_attach_storage_bucket_labels(neo4j_session):
    """
    Test that we can attach GCP storage bucket labels
    """
    _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session)
    query = """
    MATCH(bucket:GCPBucket{id:$BucketId})-[r:LABELED]->(label:GCPBucketLabel)
    RETURN bucket.id, label.key, label.value
    ORDER BY label.key
    LIMIT 1
    """
    expected_id = "bucket_name"
    expected_label_key = "label_key_1"
    expected_label_value = "label_value_1"
    nodes = neo4j_session.run(
        query,
        BucketId=expected_id,
    )
    actual_nodes = {(n["bucket.id"], n["label.key"], n["label.value"]) for n in nodes}
    expected_nodes = {
        (expected_id, expected_label_key, expected_label_value),
    }
    assert actual_nodes == expected_nodes


def _create_test_project(neo4j_session):
    # Create Test GCP Project
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id="project-abc",
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.storage,
    "get_gcp_buckets",
    return_value=tests.data.gcp.storage.STORAGE_RESPONSE,
)
def test_sync_gcp_buckets(mock_get_buckets, neo4j_session):
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "PROJECT_ID": "project-abc"}
    """Test sync_gcp_buckets() loads buckets and creates relationships."""

    # Arrange - Create test project
    _create_test_project(neo4j_session)

    # Act
    cartography.intel.gcp.storage.sync_gcp_buckets(
        neo4j_session,
        MagicMock(),
        "project-abc",
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "GCPBucket",
        ["id", "project_number", "kind"],
    ) == {
        (
            "bucket_name",
            9999,
            "storage#bucket",
        ),
    }
    assert check_nodes(
        neo4j_session,
        "GCPBucketLabel",
        ["key", "value"],
    ) == {
        ("label_key_1", "label_value_1"),
        ("label_key_2", "label_value_2"),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBucket",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "bucket_name"),
    }
    assert check_rels(
        neo4j_session,
        "GCPBucket",
        "id",
        "GCPBucketLabel",
        "id",
        "LABELED",
        rel_direction_right=True,
    ) == {
        ("bucket_name", "GCPBucket_label_key_1"),
        ("bucket_name", "GCPBucket_label_key_2"),
    }
    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPBucketLabel",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("project-abc", "GCPBucket_label_key_1"),
        ("project-abc", "GCPBucket_label_key_2"),
    }
