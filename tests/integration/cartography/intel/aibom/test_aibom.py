import copy
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


def _seed_image_resolution(
    neo4j_session,
    image_uri: str,
    digest: str,
    image_type: str,
) -> None:
    neo4j_session.run(
        """
        MERGE (img:ECRImage {id: $digest})
        SET img.digest = $digest,
            img.type = $image_type,
            img.lastupdated = $lastupdated
        MERGE (repo_img:ECRRepositoryImage {id: $image_uri})
        SET repo_img.lastupdated = $lastupdated
        MERGE (repo_img)-[r:IMAGE]->(img)
        SET r.lastupdated = $lastupdated
        """,
        digest=digest,
        image_type=image_type,
        image_uri=image_uri,
        lastupdated=TEST_UPDATE_TAG,
    )


def _seed_multi_image_resolution_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _seed_image_resolution(
        neo4j_session,
        TEST_IMAGE_URI,
        tests.data.aws.ecr.MANIFEST_LIST_DIGEST,
        "manifest_list",
    )
    _seed_image_resolution(
        neo4j_session,
        TEST_SINGLE_PLATFORM_IMAGE_URI,
        tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST,
        "image",
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
        "AIBOMSource",
        [
            "image_uri",
            "source_key",
            "scanner_name",
            "scanner_version",
            "analysis_status",
            "image_matched",
            "source_status",
            "source_kind",
            "total_components",
            "total_relationships",
        ],
    ) == {
        (
            TEST_IMAGE_URI,
            TEST_SOURCE_KEY,
            "cisco-aibom",
            "0.4.0",
            "completed",
            True,
            "completed",
            "container_image",
            6,
            4,
        ),
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

    assert check_nodes(neo4j_session, "AIAgent", ["name"]) == {
        ("pydantic_ai.Agent",),
    }
    assert check_nodes(neo4j_session, "AIModel", ["name"]) == {
        ("openai:gpt-4.1-mini",),
    }
    assert check_nodes(neo4j_session, "AITool", ["name"]) == {
        ("fetch_customer_profile",),
    }
    assert check_nodes(neo4j_session, "AIMemory", ["name"]) == {
        ("ConversationBufferMemory",),
    }
    assert check_nodes(neo4j_session, "AIPrompt", ["name"]) == {
        ("system_prompt.customer_support",),
    }

    assert check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "ECRImage",
        "type",
        "SCANNED_IMAGE",
        rel_direction_right=True,
    ) == {
        (TEST_SOURCE_KEY, "manifest_list"),
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
        "AIAgent",
        "name",
        "AIModel",
        "name",
        "USES_MODEL",
        rel_direction_right=True,
    ) == {
        ("pydantic_ai.Agent", "openai:gpt-4.1-mini"),
    }

    assert check_rels(
        neo4j_session,
        "AIAgent",
        "name",
        "AITool",
        "name",
        "USES_TOOL",
        rel_direction_right=True,
    ) == {
        ("pydantic_ai.Agent", "fetch_customer_profile"),
    }

    assert check_rels(
        neo4j_session,
        "AIAgent",
        "name",
        "AIMemory",
        "name",
        "USES_MEMORY",
        rel_direction_right=True,
    ) == {
        ("pydantic_ai.Agent", "ConversationBufferMemory"),
    }

    assert check_rels(
        neo4j_session,
        "AIAgent",
        "name",
        "AIPrompt",
        "name",
        "USES_PROMPT",
        rel_direction_right=True,
    ) == {
        ("pydantic_ai.Agent", "system_prompt.customer_support"),
    }

    assert check_nodes(
        neo4j_session,
        "AIBOMComponent",
        ["name", "framework", "label"],
    ) >= {
        (
            "pydantic_ai.Agent",
            "pydantic_ai",
            "customer_assistant",
        ),
        (
            "fetch_customer_profile",
            "internal_mcp",
            "customer_lookup_tool",
        ),
    }

    logical_id_count = neo4j_session.run(
        """
        MATCH (component:AIBOMComponent)
        WHERE component.logical_id IS NOT NULL
        RETURN count(component) AS count
        """,
    ).single()
    assert logical_id_count is not None
    assert logical_id_count["count"] == 6


def test_sync_aibom_stores_stable_logical_ids_across_images(
    neo4j_session,
    tmp_path,
):
    _seed_multi_image_resolution_graph(neo4j_session)

    second_source_key = "000000000000.dkr.ecr.us-east-1.amazonaws.com/single-platform-repository@sha256:fake"
    second_report = copy.deepcopy(AIBOM_REPORT)
    second_report["image_uri"] = TEST_SINGLE_PLATFORM_IMAGE_URI
    second_report["report"]["aibom_analysis"]["sources"] = {
        second_source_key: copy.deepcopy(
            second_report["report"]["aibom_analysis"]["sources"][TEST_SOURCE_KEY],
        ),
    }

    (tmp_path / "aibom-1.json").write_text(
        json.dumps(AIBOM_REPORT),
        encoding="utf-8",
    )
    (tmp_path / "aibom-2.json").write_text(
        json.dumps(second_report),
        encoding="utf-8",
    )

    sync_aibom_from_dir(
        neo4j_session,
        str(tmp_path),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert len(check_nodes(neo4j_session, "AIBOMComponent", ["id"])) == 12
    assert len(check_nodes(neo4j_session, "AIBOMComponent", ["logical_id"])) == 6

    row = neo4j_session.run(
        """
        MATCH (agent:AIAgent {name: 'pydantic_ai.Agent'})
        RETURN count(agent) AS detections, count(DISTINCT agent.logical_id) AS logical_ids
        """,
    ).single()
    assert row is not None
    assert row["detections"] == 2
    assert row["logical_ids"] == 1

    agent_logical_id = neo4j_session.run(
        """
        MATCH (agent:AIAgent {name: 'pydantic_ai.Agent'})
        RETURN agent.logical_id AS logical_id
        LIMIT 1
        """,
    ).single()["logical_id"]

    assert check_rels(
        neo4j_session,
        "AIAgent",
        "logical_id",
        "ECRImage",
        "digest",
        "DETECTED_IN",
        rel_direction_right=True,
    ) >= {
        (agent_logical_id, tests.data.aws.ecr.MANIFEST_LIST_DIGEST),
        (agent_logical_id, tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST),
    }


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="",
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-relationship-fallback.json"},
)
def test_sync_aibom_relationship_falls_back_to_name_category_when_instance_id_unmatched(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_manifest_list_graph(neo4j_session)

    report = copy.deepcopy(AIBOM_REPORT)
    relationship = report["report"]["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
        "relationships"
    ][0]
    relationship["source"]["instance_id"] = "missing-agent-instance"
    relationship["target"]["instance_id"] = "missing-model-instance"
    mock_file_open.return_value.read.return_value = json.dumps(report)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert (
        "pydantic_ai.Agent",
        "openai:gpt-4.1-mini",
    ) in check_rels(
        neo4j_session,
        "AIAgent",
        "name",
        "AIModel",
        "name",
        "USES_MODEL",
        rel_direction_right=True,
    )


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="",
)
@patch(
    "cartography.intel.aibom._get_json_files_in_dir",
    return_value={"/tmp/aibom-flat-source-target.json"},
)
def test_sync_aibom_parses_flat_source_target_relationships(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_manifest_list_graph(neo4j_session)

    report = copy.deepcopy(AIBOM_REPORT)
    relationship = report["report"]["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
        "relationships"
    ][1]
    relationship.pop("source")
    relationship.pop("target")
    relationship.update(
        {
            "source_instance_id": "agent_main",
            "source_name": "pydantic_ai.Agent",
            "source_category": "agent",
            "target_instance_id": "tool_customer_lookup",
            "target_name": "fetch_customer_profile",
            "target_category": "tool",
        },
    )
    mock_file_open.return_value.read.return_value = json.dumps(report)

    sync_aibom_from_dir(
        neo4j_session,
        "/tmp",
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert (
        "pydantic_ai.Agent",
        "fetch_customer_profile",
    ) in check_rels(
        neo4j_session,
        "AIAgent",
        "name",
        "AITool",
        "name",
        "USES_TOOL",
        rel_direction_right=True,
    )


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
        "AIBOMSource",
        ["image_uri", "image_matched", "source_key", "source_status"],
    ) == {
        (TEST_IMAGE_URI, True, TEST_SOURCE_KEY, "failed"),
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
        "AIBOMSource",
        ["image_uri", "image_matched", "source_key", "source_status"],
    ) == {
        (
            "000000000000.dkr.ecr.us-east-1.amazonaws.com/unmatched-repository:v1.0",
            False,
            TEST_SOURCE_KEY,
            "completed",
        ),
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
        "AIBOMSource",
        "source_key",
        "ECRImage",
        "type",
        "SCANNED_IMAGE",
        rel_direction_right=True,
    ) == {
        (TEST_SOURCE_KEY, "image"),
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

    assert check_nodes(neo4j_session, "AIBOMSource", ["id"]) == set()
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

    assert check_nodes(neo4j_session, "AIBOMSource", ["id"]) == set()
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
        """
    )

    cleanup_aibom(neo4j_session, {"UPDATE_TAG": TEST_UPDATE_TAG})

    assert "stale-source" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMSource", ["id"])
    }
    assert "stale-component" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMComponent", ["id"])
    }
    assert "stale-workflow" not in {
        row[0] for row in check_nodes(neo4j_session, "AIBOMWorkflow", ["id"])
    }

    assert len(check_nodes(neo4j_session, "AIBOMSource", ["id"])) == 1
    assert len(check_nodes(neo4j_session, "AIBOMComponent", ["id"])) == 6
    assert len(check_nodes(neo4j_session, "AIBOMWorkflow", ["id"])) == 2
