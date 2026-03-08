import datetime
import json
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import cartography.intel.aws.ecr
import tests.data.aws.ecr
from cartography.intel.aibom import sync_aibom_from_dir
from cartography.intel.aibom import sync_aibom_from_s3
from cartography.intel.aibom.cleanup import cleanup_aibom
from tests.data.aibom.aibom_sample import AIBOM_INCOMPLETE_REPORT
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import AIBOM_SINGLE_PLATFORM_REPORT
from tests.data.aibom.aibom_sample import AIBOM_UNMATCHED_REPORT
from tests.data.aibom.aibom_sample import TEST_IMAGE_URI
from tests.data.aibom.aibom_sample import TEST_SINGLE_PLATFORM_IMAGE_URI
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


def _seed_manifest_list_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    boto3_session = MagicMock()
    mock_client = MagicMock()

    # list_images -> one tagged manifest-list image
    mock_list_paginator = MagicMock()
    mock_list_paginator.paginate.return_value = [
        {
            "imageIds": [
                {
                    "imageDigest": tests.data.aws.ecr.MANIFEST_LIST_DIGEST,
                    "imageTag": "v1.0",
                }
            ]
        }
    ]

    # describe_images -> manifest-list metadata
    mock_describe_paginator = MagicMock()
    mock_describe_paginator.paginate.return_value = [
        {"imageDetails": [tests.data.aws.ecr.MULTI_ARCH_IMAGE_DETAILS]}
    ]

    def get_paginator(name):
        if name == "list_images":
            return mock_list_paginator
        if name == "describe_images":
            return mock_describe_paginator
        raise ValueError(f"Unexpected paginator: {name}")

    mock_client.get_paginator = get_paginator
    mock_client.batch_get_image.return_value = (
        tests.data.aws.ecr.BATCH_GET_MANIFEST_LIST_RESPONSE
    )
    boto3_session.client.return_value = mock_client

    with patch.object(
        cartography.intel.aws.ecr,
        "get_ecr_repositories",
        return_value=[
            {
                "repositoryArn": f"arn:aws:ecr:{TEST_REGION}:{TEST_ACCOUNT_ID}:repository/multi-arch-repository",
                "registryId": TEST_ACCOUNT_ID,
                "repositoryName": "multi-arch-repository",
                "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/multi-arch-repository",
                "createdAt": datetime.datetime(2025, 1, 1, 0, 0, 1),
            }
        ],
    ):
        cartography.intel.aws.ecr.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )


def _assert_seed_is_manifest_list_shape(neo4j_session) -> None:
    image_uri = neo4j_session.run(
        """
        MATCH (ri:ECRRepositoryImage)
        RETURN ri.id AS id
        """
    ).single()["id"]
    assert image_uri == TEST_IMAGE_URI

    manifest_types = neo4j_session.run(
        """
        MATCH (:ECRRepositoryImage {id: $image_uri})-[:IMAGE]->(img:ECRImage)
        RETURN collect(DISTINCT img.type) AS types
        """,
        image_uri=TEST_IMAGE_URI,
    ).single()["types"]

    assert "manifest_list" in manifest_types
    assert "image" in manifest_types


def _seed_single_platform_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    boto3_session = MagicMock()
    mock_client = MagicMock()

    mock_list_paginator = MagicMock()
    mock_list_paginator.paginate.return_value = [
        {
            "imageIds": [
                {
                    "imageDigest": tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST,
                    "imageTag": "latest",
                }
            ]
        }
    ]

    mock_describe_paginator = MagicMock()
    mock_describe_paginator.paginate.return_value = [
        {"imageDetails": [tests.data.aws.ecr.SINGLE_PLATFORM_IMAGE_DETAILS]}
    ]

    def get_paginator(name):
        if name == "list_images":
            return mock_list_paginator
        if name == "describe_images":
            return mock_describe_paginator
        raise ValueError(f"Unexpected paginator: {name}")

    mock_client.get_paginator = get_paginator
    mock_client.batch_get_image.return_value = (
        tests.data.aws.ecr.BATCH_GET_MANIFEST_LIST_EMPTY_RESPONSE
    )
    boto3_session.client.return_value = mock_client

    with patch.object(
        cartography.intel.aws.ecr,
        "get_ecr_repositories",
        return_value=[
            {
                "repositoryArn": f"arn:aws:ecr:{TEST_REGION}:{TEST_ACCOUNT_ID}:repository/single-platform-repository",
                "registryId": TEST_ACCOUNT_ID,
                "repositoryName": "single-platform-repository",
                "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository",
                "createdAt": datetime.datetime(2025, 1, 1, 0, 0, 1),
            }
        ],
    ):
        cartography.intel.aws.ecr.sync(
            neo4j_session,
            boto3_session,
            [TEST_REGION],
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
        )


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom.json"},
)
def test_sync_aibom_from_dir(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_manifest_list_graph(neo4j_session)
    _assert_seed_is_manifest_list_shape(neo4j_session)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    category_counts = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)
        RETURN c.category AS category, count(*) AS count
        ORDER BY category
        """,
    ).data()

    assert category_counts == [
        {"category": "agent", "count": 1},
        {"category": "other", "count": 1},
        {"category": "tool", "count": 1},
    ]

    workflow_nodes = check_nodes(neo4j_session, "AIBOMWorkflow", ["workflow_id"])
    assert workflow_nodes == {
        ("workflow-agent",),
        ("workflow-tool",),
    }

    in_workflow_count = neo4j_session.run(
        """
        MATCH (:AIBOMComponent)-[r:IN_WORKFLOW]->(:AIBOMWorkflow)
        RETURN count(r) AS count
        """,
    ).single()["count"]
    assert in_workflow_count == 2

    detected_types = neo4j_session.run(
        """
        MATCH (:AIBOMComponent)-[:DETECTED_IN]->(img:ECRImage)
        RETURN DISTINCT img.type AS type
        """,
    ).data()
    assert detected_types == [{"type": "manifest_list"}]

    detected_platform_images = neo4j_session.run(
        """
        MATCH (:AIBOMComponent)-[:DETECTED_IN]->(img:ECRImage {type: 'image'})
        RETURN count(img) AS count
        """,
    ).single()["count"]
    assert detected_platform_images == 0

    # Verify envelope fields are stored on components
    row = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)
        RETURN c.source_image_uri AS source_image_uri,
               c.scanner_name AS scanner_name,
               c.scanner_version AS scanner_version,
               c.scan_scope AS scan_scope
        LIMIT 1
        """,
    ).single()

    assert row["source_image_uri"] == TEST_IMAGE_URI
    assert row["scanner_name"] == "cisco-aibom"
    assert row["scanner_version"] == "0.4.0"
    assert row["scan_scope"] == "/app/app"


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_INCOMPLETE_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-incomplete.json"},
)
def test_sync_aibom_skips_incomplete_sources(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_manifest_list_graph(neo4j_session)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    counts = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)
        RETURN count(c) AS count
        """,
    ).single()["count"]
    assert counts == 0


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_UNMATCHED_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-unmatched.json"},
)
def test_sync_aibom_skips_unmatched_sources(
    mock_json_files,
    mock_file_open,
    neo4j_session,
    caplog,
):
    _seed_manifest_list_graph(neo4j_session)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    component_count = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)
        RETURN count(c) AS count
        """,
    ).single()["count"]
    assert component_count == 0
    assert "could not resolve digest" in caplog.text


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_SINGLE_PLATFORM_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-single-platform.json"},
)
def test_sync_aibom_falls_back_to_single_platform_image(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_single_platform_graph(neo4j_session)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    row = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)-[:DETECTED_IN]->(img:ECRImage)
        RETURN c.source_image_uri AS source_image_uri, img.type AS type, img.digest AS digest
        """,
    ).single()

    assert row["source_image_uri"] == TEST_SINGLE_PLATFORM_IMAGE_URI
    assert row["type"] == "image"
    assert row["digest"] == tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST


@patch(
    "builtins.open",
    side_effect=UnicodeDecodeError("utf-8", b"\x80", 0, 1, "invalid start byte"),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-bad-encoding.json"},
)
def test_sync_aibom_skips_local_unicode_decode_errors(
    mock_json_files,
    mock_file_open,
    neo4j_session,
    caplog,
):
    _seed_manifest_list_graph(neo4j_session)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    component_count = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)
        RETURN count(c) AS count
        """,
    ).single()["count"]
    assert component_count == 0
    assert (
        "Skipping unreadable AIBOM report /tmp/aibom-bad-encoding.json" in caplog.text
    )


def test_sync_aibom_skips_s3_unicode_decode_errors(
    neo4j_session,
    caplog,
):
    _seed_manifest_list_graph(neo4j_session)

    boto3_session = MagicMock()
    s3_client = MagicMock()
    s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=b"\x80")),
    }
    boto3_session.client.return_value = s3_client

    with patch(
        "cartography.intel.aibom._get_json_files_in_s3",
        return_value={"reports/aibom-bad-encoding.json"},
    ):
        sync_aibom_from_s3(
            neo4j_session,
            "example-bucket",
            "reports/",
            TEST_UPDATE_TAG,
            {"UPDATE_TAG": TEST_UPDATE_TAG},
            boto3_session,
        )

    component_count = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent)
        RETURN count(c) AS count
        """,
    ).single()["count"]
    assert component_count == 0
    assert (
        "Skipping unreadable AIBOM report s3://example-bucket/reports/aibom-bad-encoding.json"
        in caplog.text
    )


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-cleanup.json"},
)
def test_cleanup_aibom_removes_stale_nodes(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_manifest_list_graph(neo4j_session)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    neo4j_session.run(
        """
        CREATE (:AIBOMComponent {
            id: 'stale-component',
            lastupdated: 0,
            _module_name: 'cartography:aibom'
        })
        CREATE (:AIBOMWorkflow {
            id: 'stale-workflow',
            lastupdated: 0,
            _module_name: 'cartography:aibom'
        })
        """
    )

    cleanup_aibom(neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG})

    stale_component_count = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent {id: 'stale-component'})
        RETURN count(c) AS count
        """,
    ).single()["count"]
    stale_workflow_count = neo4j_session.run(
        """
        MATCH (w:AIBOMWorkflow {id: 'stale-workflow'})
        RETURN count(w) AS count
        """,
    ).single()["count"]
    assert stale_component_count == 0
    assert stale_workflow_count == 0

    current_component_count = neo4j_session.run(
        """
        MATCH (c:AIBOMComponent {lastupdated: $update_tag})
        RETURN count(c) AS count
        """,
        update_tag=TEST_UPDATE_TAG,
    ).single()["count"]
    current_workflow_count = neo4j_session.run(
        """
        MATCH (w:AIBOMWorkflow {lastupdated: $update_tag})
        RETURN count(w) AS count
        """,
        update_tag=TEST_UPDATE_TAG,
    ).single()["count"]

    assert current_component_count == 3
    assert current_workflow_count == 2
