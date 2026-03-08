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
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_REGION = "us-east-1"


def _seed_manifest_list_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    boto3_session = MagicMock()
    mock_client = MagicMock()

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

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_nodes(
        neo4j_session,
        "AIBOMScan",
        [
            "image_uri",
            "scanner_name",
            "scanner_version",
            "analysis_status",
            "image_matched",
        ],
    ) == {
        (TEST_IMAGE_URI, "cisco-aibom", "0.4.0", "completed", True),
    }

    assert check_nodes(
        neo4j_session,
        "AIBOMSource",
        [
            "source_key",
            "source_status",
            "source_kind",
            "total_components",
            "total_relationships",
        ],
    ) == {
        (TEST_SOURCE_KEY, "completed", "container_image", 6, 4),
    }

    assert check_nodes(neo4j_session, "AIBOMComponent", ["category"]) == {
        ("agent",),
        ("memory",),
        ("model",),
        ("other",),
        ("prompt",),
        ("tool",),
    }

    assert check_nodes(neo4j_session, "AIBOMWorkflow", ["workflow_id"]) == {
        ("workflow-agent",),
        ("workflow-tool",),
    }

    assert check_nodes(neo4j_session, "AIBOMRelationship", ["relationship_type"]) == {
        ("USES_LLM",),
        ("USES_MEMORY",),
        ("USES_PROMPT",),
        ("USES_TOOL",),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMScan",
        "image_uri",
        "ECRImage",
        "type",
        "SCANNED_IMAGE",
        rel_direction_right=True,
    ) == {
        (TEST_IMAGE_URI, "manifest_list"),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMScan",
        "image_uri",
        "AIBOMSource",
        "source_key",
        "HAS_SOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_IMAGE_URI, TEST_SOURCE_KEY),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "AIBOMComponent",
        "category",
        "HAS_COMPONENT",
        rel_direction_right=True,
    ) == {
        (TEST_SOURCE_KEY, "agent"),
        (TEST_SOURCE_KEY, "memory"),
        (TEST_SOURCE_KEY, "model"),
        (TEST_SOURCE_KEY, "other"),
        (TEST_SOURCE_KEY, "prompt"),
        (TEST_SOURCE_KEY, "tool"),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMComponent",
        "name",
        "AIBOMWorkflow",
        "workflow_id",
        "IN_WORKFLOW",
        rel_direction_right=True,
    ) == {
        ("ConversationBufferMemory", "workflow-agent"),
        ("fetch_customer_profile", "workflow-tool"),
        ("openai:gpt-4.1-mini", "workflow-agent"),
        ("pydantic_ai.Agent", "workflow-agent"),
        ("system_prompt.customer_support", "workflow-agent"),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMComponent",
        "name",
        "AIBOMRelationship",
        "relationship_type",
        "FROM_COMPONENT",
        rel_direction_right=True,
    ) == {
        ("pydantic_ai.Agent", "USES_LLM"),
        ("pydantic_ai.Agent", "USES_MEMORY"),
        ("pydantic_ai.Agent", "USES_PROMPT"),
        ("pydantic_ai.Agent", "USES_TOOL"),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMRelationship",
        "relationship_type",
        "AIBOMComponent",
        "name",
        "TO_COMPONENT",
        rel_direction_right=True,
    ) == {
        ("USES_LLM", "openai:gpt-4.1-mini"),
        ("USES_MEMORY", "ConversationBufferMemory"),
        ("USES_PROMPT", "system_prompt.customer_support"),
        ("USES_TOOL", "fetch_customer_profile"),
    }

    assert check_nodes(
        neo4j_session,
        "AIBOMComponent",
        ["name", "framework", "label", "metadata_json"],
    ) >= {
        (
            "pydantic_ai.Agent",
            "pydantic_ai",
            "customer_assistant",
            json.dumps({"approval": "human", "mcp": True}, sort_keys=True),
        ),
        (
            "fetch_customer_profile",
            "internal_mcp",
            "customer_lookup_tool",
            json.dumps({"approval": "required", "transport": "mcp"}, sort_keys=True),
        ),
    }


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_INCOMPLETE_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-incomplete.json"},
)
def test_sync_aibom_keeps_scan_provenance_for_incomplete_sources(
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

    assert check_nodes(
        neo4j_session,
        "AIBOMScan",
        ["image_uri", "image_matched"],
    ) == {
        (TEST_IMAGE_URI, True),
    }
    assert check_nodes(
        neo4j_session,
        "AIBOMSource",
        ["source_key", "source_status"],
    ) == {
        (TEST_SOURCE_KEY, "failed"),
    }
    assert check_nodes(neo4j_session, "AIBOMComponent", ["id"]) == set()


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_UNMATCHED_REPORT),
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-unmatched.json"},
)
def test_sync_aibom_keeps_scan_provenance_for_unmatched_sources(
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

    assert check_nodes(
        neo4j_session,
        "AIBOMScan",
        ["image_uri", "image_matched"],
    ) == {
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/unmatched-repository:v1.0",
            False,
        ),
    }
    assert check_nodes(
        neo4j_session,
        "AIBOMSource",
        ["source_key", "source_status"],
    ) == {
        (TEST_SOURCE_KEY, "completed"),
    }
    assert check_nodes(neo4j_session, "AIBOMComponent", ["id"]) == set()
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

    assert check_rels(
        neo4j_session,
        "AIBOMScan",
        "image_uri",
        "ECRImage",
        "type",
        "SCANNED_IMAGE",
        rel_direction_right=True,
    ) == {
        (TEST_SINGLE_PLATFORM_IMAGE_URI, "image"),
    }


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

    assert check_nodes(neo4j_session, "AIBOMScan", ["id"]) == set()
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

    assert check_nodes(neo4j_session, "AIBOMScan", ["id"]) == set()
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
        CREATE (:AIBOMScan {
            id: 'stale-scan',
            lastupdated: 0,
            _module_name: 'cartography:aibom'
        })
        CREATE (:AIBOMSource {
            id: 'stale-source',
            lastupdated: 0,
            _module_name: 'cartography:aibom'
        })
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
        CREATE (:AIBOMRelationship {
            id: 'stale-relationship',
            lastupdated: 0,
            _module_name: 'cartography:aibom'
        })
        """
    )

    cleanup_aibom(neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG})

    assert "stale-scan" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMScan", ["id"])
    }
    assert "stale-source" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMSource", ["id"])
    }
    assert "stale-component" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMComponent", ["id"])
    }
    assert "stale-workflow" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMWorkflow", ["id"])
    }
    assert "stale-relationship" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMRelationship", ["id"])
    }

    assert len(check_nodes(neo4j_session, "AIBOMScan", ["id"])) == 1
    assert len(check_nodes(neo4j_session, "AIBOMSource", ["id"])) == 1
    assert len(check_nodes(neo4j_session, "AIBOMComponent", ["id"])) == 6
    assert len(check_nodes(neo4j_session, "AIBOMWorkflow", ["id"])) == 2
    assert len(check_nodes(neo4j_session, "AIBOMRelationship", ["id"])) == 4
