import cartography.intel.gcp.storage
import tests.data.gcp.storage

TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_storage_bucket_data(neo4j_session):
    bucket_res = tests.data.gcp.storage.STORAGE_RESPONSE
    bucket_list = cartography.intel.gcp.storage.transform_gcp_buckets(bucket_res)
    cartography.intel.gcp.storage.load_gcp_buckets(
        neo4j_session,
        bucket_list,
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
