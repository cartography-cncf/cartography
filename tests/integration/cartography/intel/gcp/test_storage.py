from unittest.mock import patch

import cartography.intel.gcp.storage
import tests.data.gcp.storage
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

OLD_UPDATE_TAG = 12345
NEW_UPDATE_TAG = 67890
TEST_PROJECT_NUMBER = "9999"
TEST_PROJECT_ID_STRING = f"project-{TEST_PROJECT_NUMBER}"


def _ensure_local_neo4j_has_test_storage_data(neo4j_session, update_tag):
    """
    A single, clean helper to transform and load all test data into the graph.
    """
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id:$ProjectNumber, projectnumber: $ProjectNumber})
        ON CREATE SET p.firstseen = timestamp()
        SET p.lastupdated = $UpdateTag, p.projectid = $ProjectIdString
        """,
        ProjectNumber=TEST_PROJECT_NUMBER,
        ProjectIdString=TEST_PROJECT_ID_STRING,
        UpdateTag=update_tag,
    )

    bucket_res = tests.data.gcp.storage.STORAGE_RESPONSE["items"]
    bucket_list = cartography.intel.gcp.storage.transform_gcp_buckets(bucket_res)

    all_labels = []
    for bucket in bucket_list:
        all_labels.extend(bucket.get("labels", []))

    if all_labels:
        cartography.intel.gcp.storage.load_gcp_labels(
            neo4j_session,
            all_labels,
            TEST_PROJECT_NUMBER,
            update_tag,
        )
    cartography.intel.gcp.storage.load_gcp_buckets(
        neo4j_session,
        bucket_list,
        TEST_PROJECT_NUMBER,
        update_tag,
    )


def test_transform_and_load_storage_buckets(neo4j_session):
    _ensure_local_neo4j_has_test_storage_data(neo4j_session, OLD_UPDATE_TAG)
    expected_nodes = {
        ("bucket_name", TEST_PROJECT_NUMBER, "storage#bucket"),
    }
    actual_nodes = check_nodes(
        neo4j_session,
        "GCPBucket",
        ["id", "project_number", "kind"],
    )
    assert actual_nodes == expected_nodes
    expected_rels = {
        (TEST_PROJECT_NUMBER, "bucket_name"),
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
    _ensure_local_neo4j_has_test_storage_data(neo4j_session, OLD_UPDATE_TAG)
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


@patch("cartography.intel.gcp.storage.get_gcp_buckets")
def test_sync_removes_stale_buckets_and_labels(mock_get, neo4j_session):
    """
    Test that the sync function correctly removes stale buckets and their labels.
    """
    _ensure_local_neo4j_has_test_storage_data(neo4j_session, OLD_UPDATE_TAG)
    assert check_nodes(neo4j_session, "GCPBucket", ["id"])
    assert check_nodes(neo4j_session, "GCPBucketLabel", ["id"])

    mock_get.return_value = []

    common_job_parameters = {"UPDATE_TAG": NEW_UPDATE_TAG}
    common_job_parameters["project_number"] = TEST_PROJECT_NUMBER

    cartography.intel.gcp.storage.sync_gcp_buckets(
        neo4j_session,
        None,
        TEST_PROJECT_ID_STRING,
        NEW_UPDATE_TAG,
        common_job_parameters,
    )

    assert not check_nodes(neo4j_session, "GCPBucket", ["id"])
    assert not check_nodes(neo4j_session, "GCPBucketLabel", ["id"])
