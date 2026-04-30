from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.storage
import tests.data.gcp.storage
from cartography.intel.gcp.labels import sync_labels
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
    expected_project_num = 123456789012
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
        ["id", "project_number", "kind", "iam_config_public_access_prevention"],
    ) == {
        (
            "bucket_name",
            123456789012,
            "storage#bucket",
            "inherited",
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
    # GCPBucketLabel nodes include both legacy (GCPBucketLabelSchema) and
    # unified (GCPBucketGCPLabelSchema) nodes since both carry the GCPBucketLabel label.
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
        ("bucket_name", "bucket_name:label_key_1:label_value_1"),
        ("bucket_name", "bucket_name:label_key_2:label_value_2"),
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
        ("project-abc", "bucket_name:label_key_1:label_value_1"),
        ("project-abc", "bucket_name:label_key_2:label_value_2"),
    }

    # Assert - unified GCPLabel nodes created by sync_labels
    assert check_nodes(
        neo4j_session,
        "GCPLabel",
        ["id", "key", "value", "resource_type"],
    ) == {
        (
            "bucket_name:label_key_1:label_value_1",
            "label_key_1",
            "label_value_1",
            "GCPBucket",
        ),
        (
            "bucket_name:label_key_2:label_value_2",
            "label_key_2",
            "label_value_2",
            "GCPBucket",
        ),
    }
    # Assert - LABELED relationships from bucket to GCPLabel
    assert check_rels(
        neo4j_session,
        "GCPBucket",
        "id",
        "GCPLabel",
        "id",
        "LABELED",
        rel_direction_right=True,
    ) == {
        ("bucket_name", "bucket_name:label_key_1:label_value_1"),
        ("bucket_name", "bucket_name:label_key_2:label_value_2"),
    }


def test_sync_labels_cleanup_is_scoped_per_resource_type(neo4j_session):
    """
    Verify that syncing one resource type does not delete stale labels for other resource types.
    """
    project_id = "project-abc"
    bucket_id = "bucket-scope-test"
    instance_id = (
        "projects/project-abc/zones/us-central1-a/instances/instance-scope-test"
    )

    _create_test_project(neo4j_session)
    neo4j_session.run(
        """
        MATCH (p:GCPProject {id: $project_id})
        MERGE (b:GCPBucket {id: $bucket_id})
        MERGE (i:GCPInstance {id: $instance_id})
        SET b.lastupdated = $seed_tag, i.lastupdated = $seed_tag
        MERGE (p)-[rb:RESOURCE]->(b)
        MERGE (p)-[ri:RESOURCE]->(i)
        SET rb.lastupdated = $seed_tag, ri.lastupdated = $seed_tag
        """,
        project_id=project_id,
        bucket_id=bucket_id,
        instance_id=instance_id,
        seed_tag=1,
    )

    seed_common_job_parameters = {"UPDATE_TAG": 100, "PROJECT_ID": project_id}
    sync_labels(
        neo4j_session,
        [{"id": bucket_id, "labels": {"team": "security"}}],
        "gcp_bucket",
        project_id,
        100,
        seed_common_job_parameters,
    )
    sync_labels(
        neo4j_session,
        [{"partial_uri": instance_id, "labels": {"env": "prod"}}],
        "gcp_instance",
        project_id,
        100,
        seed_common_job_parameters,
    )

    refresh_common_job_parameters = {"UPDATE_TAG": 200, "PROJECT_ID": project_id}
    sync_labels(
        neo4j_session,
        [{"id": bucket_id, "labels": {"team": "platform"}}],
        "gcp_bucket",
        project_id,
        200,
        refresh_common_job_parameters,
    )

    instance_label_rows = neo4j_session.run(
        """
        MATCH (l:GCPLabel {id: $instance_label_id})
        RETURN l.lastupdated AS lastupdated, l.resource_type AS resource_type
        """,
        instance_label_id=f"{instance_id}:env:prod",
    ).data()
    assert instance_label_rows == [
        {"lastupdated": 100, "resource_type": "GCPInstance"},
    ]

    all_label_ids = {
        row["id"]
        for row in neo4j_session.run(
            "MATCH (l:GCPLabel) RETURN l.id AS id ORDER BY id",
        ).data()
    }
    assert f"{bucket_id}:team:security" not in all_label_ids
    assert f"{bucket_id}:team:platform" in all_label_ids
    assert f"{instance_id}:env:prod" in all_label_ids
