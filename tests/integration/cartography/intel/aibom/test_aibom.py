import copy
import datetime
import json
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import cartography.intel.aws.ecr
import tests.data.aws.ecr
from cartography.intel.aibom import sync_aibom_from_report_reader
from cartography.intel.common.object_store import LocalReportReader
from cartography.intel.common.object_store import ReportRef
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import build_repo_anchored_report
from tests.data.aibom.aibom_sample import TEST_GITHUB_REPO_URL
from tests.data.aibom.aibom_sample import TEST_GITLAB_PROJECT_URL
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
TEST_UPDATE_TAG_2 = 123456790
TEST_REGION = "us-east-1"


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


def _seed_github_repository(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (r:GitHubRepository {id: $url})
        SET r.url = $url, r.lastupdated = $update_tag
        """,
        url=TEST_GITHUB_REPO_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _seed_gitlab_project(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (p:GitLabProject {id: $id})
        SET p.web_url = $web_url, p.lastupdated = $update_tag
        """,
        id="42",
        web_url=TEST_GITLAB_PROJECT_URL,
        update_tag=TEST_UPDATE_TAG,
    )


def _build_report_without_component(
    report: dict,
    component_bucket: str,
    component_name: str,
) -> dict:
    trimmed_report = copy.deepcopy(report)
    analysis = trimmed_report["aibom_analysis"]
    source_data = analysis["sources"][TEST_SOURCE_KEY]
    components = source_data["components"][component_bucket]

    source_data["components"][component_bucket] = [
        component for component in components if component["name"] != component_name
    ]
    if not source_data["components"][component_bucket]:
        del source_data["components"][component_bucket]

    source_summary = source_data["summary"]
    source_summary["assets_discovered"] -= 1

    report_summary = analysis["summary"]
    report_summary["total_components"] -= 1
    report_summary["component_types"][component_bucket] -= 1
    if report_summary["component_types"][component_bucket] == 0:
        del report_summary["component_types"][component_bucket]

    return trimmed_report


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(AIBOM_REPORT).encode("utf-8"),
)
@patch(
    "cartography.intel.common.object_store.LocalReportReader.list_reports",
    return_value=[ReportRef(uri="/tmp/aibom.json", name="aibom.json")],
)
def test_sync_aibom_happy_path(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    _seed_single_platform_graph(neo4j_session)

    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader("/tmp"),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_nodes(
        neo4j_session,
        "AIBOMSource",
        ["source_key"],
    ) == {
        (TEST_SOURCE_KEY,),
    }

    component_nodes = check_nodes(
        neo4j_session,
        "AIBOMComponent",
        ["name"],
    )
    assert component_nodes is not None
    assert len(component_nodes) > 0

    assert check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "Image",
        "_ont_digest",
        "SCANNED_IMAGE",
        rel_direction_right=True,
    ) == {
        (TEST_SOURCE_KEY, tests.data.aws.ecr.SINGLE_PLATFORM_DIGEST),
    }

    has_component_rels = check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "AIBOMComponent",
        "name",
        "HAS_COMPONENT",
        rel_direction_right=True,
    )
    assert len(has_component_rels) == len(component_nodes)

    detected_in_rels = check_rels(
        neo4j_session,
        "AIBOMComponent",
        "name",
        "Image",
        "_ont_digest",
        "DETECTED_IN",
        rel_direction_right=True,
    )
    assert len(detected_in_rels) == len(component_nodes)

    assert check_rels(
        neo4j_session,
        "AIBOMComponent",
        "name",
        "AIBOMComponent",
        "name",
        "USES_MODEL",
        rel_direction_right=True,
    ) == {
        ("Agent", "gpt-5.2"),
    }

    # Assert the same relationships are traversable through the AI-specific labels used by downstream rules.
    assert check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "AIAgent",
        "name",
        "HAS_COMPONENT",
        rel_direction_right=True,
    ) == {
        (TEST_SOURCE_KEY, "Agent"),
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
        ("Agent", "gpt-5.2"),
    }

    ai_labeled_components = neo4j_session.run(
        """
        MATCH (component:AIBOMComponent)
        WHERE component.name IN ['Agent', 'gpt-5.2', 'subimageGetTicket']
        RETURN component.name AS name,
               component:AIAgent AS is_agent,
               component:AIModel AS is_model,
               component:AITool AS is_tool
        ORDER BY component.name
        """,
    ).data()
    assert ai_labeled_components == [
        {
            "name": "Agent",
            "is_agent": True,
            "is_model": False,
            "is_tool": False,
        },
        {
            "name": "gpt-5.2",
            "is_agent": False,
            "is_model": True,
            "is_tool": False,
        },
        {
            "name": "subimageGetTicket",
            "is_agent": False,
            "is_model": False,
            "is_tool": True,
        },
    ]


@patch(
    "builtins.open",
    new_callable=mock_open,
)
@patch(
    "cartography.intel.common.object_store.LocalReportReader.list_reports",
    return_value=[ReportRef(uri="/tmp/aibom.json", name="aibom.json")],
)
def test_sync_aibom_cleanup_removes_stale_components_after_second_snapshot(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    # Arrange
    _seed_single_platform_graph(neo4j_session)
    trimmed_report = _build_report_without_component(
        AIBOM_REPORT,
        component_bucket="secret",
        component_name="vault-secret",
    )
    mock_file_open.return_value.read.side_effect = [
        json.dumps(AIBOM_REPORT).encode("utf-8"),
        json.dumps(trimmed_report).encode("utf-8"),
    ]

    # Act
    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader("/tmp"),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )
    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader("/tmp"),
        TEST_UPDATE_TAG_2,
        {"UPDATE_TAG": TEST_UPDATE_TAG_2},
    )

    # Assert
    component_nodes = check_nodes(
        neo4j_session,
        "AIBOMComponent",
        ["name"],
    )
    assert component_nodes is not None
    assert ("vault-secret",) not in component_nodes

    expected_component_count = sum(
        len(items)
        for items in trimmed_report["aibom_analysis"]["sources"][TEST_SOURCE_KEY][
            "components"
        ].values()
    )
    assert len(component_nodes) == expected_component_count

    has_component_rels = check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "AIBOMComponent",
        "name",
        "HAS_COMPONENT",
        rel_direction_right=True,
    )
    assert len(has_component_rels) == expected_component_count


@patch(
    "builtins.open",
    new_callable=mock_open,
)
@patch(
    "cartography.intel.common.object_store.LocalReportReader.list_reports",
    return_value=[ReportRef(uri="/tmp/aibom.json", name="aibom.json")],
)
def test_sync_aibom_skips_ambiguous_type_name_relationship_endpoints(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    # Arrange
    _seed_single_platform_graph(neo4j_session)
    ambiguous_report = copy.deepcopy(AIBOM_REPORT)
    source_data = ambiguous_report["aibom_analysis"]["sources"][TEST_SOURCE_KEY]
    # Add a duplicate model endpoint (same source/type/name) with different
    # identity fields so fallback type/name resolution becomes ambiguous.
    source_data["components"]["model"].append(
        {
            **copy.deepcopy(source_data["components"]["model"][0]),
            "file_path": "/tmp/ambiguous_model.py",
            "line_number": 4242,
        },
    )
    mock_file_open.return_value.read.return_value = json.dumps(ambiguous_report).encode(
        "utf-8",
    )

    # Act
    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader("/tmp"),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "AIBOMComponent",
            "name",
            "AIBOMComponent",
            "name",
            "USES_MODEL",
            rel_direction_right=True,
        )
        == set()
    )


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(build_repo_anchored_report(TEST_GITHUB_REPO_URL)).encode(
        "utf-8"
    ),
)
@patch(
    "cartography.intel.common.object_store.LocalReportReader.list_reports",
    return_value=[ReportRef(uri="/tmp/aibom.json", name="aibom.json")],
)
def test_sync_aibom_links_components_to_github_repository(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    # Arrange
    _seed_github_repository(neo4j_session)

    # Act
    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader("/tmp"),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AIBOMSource",
        ["source_key"],
    ) == {
        (TEST_GITHUB_REPO_URL,),
    }

    component_nodes = check_nodes(
        neo4j_session,
        "AIBOMComponent",
        ["name"],
    )
    assert component_nodes is not None
    assert len(component_nodes) > 0

    assert check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "GitHubRepository",
        "url",
        "SCANNED_REPOSITORY",
        rel_direction_right=True,
    ) == {
        (TEST_GITHUB_REPO_URL, TEST_GITHUB_REPO_URL),
    }

    detected_in_rels = check_rels(
        neo4j_session,
        "AIBOMComponent",
        "name",
        "GitHubRepository",
        "url",
        "DETECTED_IN",
        rel_direction_right=True,
    )
    assert len(detected_in_rels) == len(component_nodes)


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps(build_repo_anchored_report(TEST_GITLAB_PROJECT_URL)).encode(
        "utf-8"
    ),
)
@patch(
    "cartography.intel.common.object_store.LocalReportReader.list_reports",
    return_value=[ReportRef(uri="/tmp/aibom.json", name="aibom.json")],
)
def test_sync_aibom_links_components_to_gitlab_project(
    mock_json_files,
    mock_file_open,
    neo4j_session,
):
    # Arrange
    _seed_gitlab_project(neo4j_session)

    # Act
    sync_aibom_from_report_reader(
        neo4j_session,
        LocalReportReader("/tmp"),
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_nodes(
        neo4j_session,
        "AIBOMSource",
        ["source_key"],
    ) == {
        (TEST_GITLAB_PROJECT_URL,),
    }

    component_nodes = check_nodes(
        neo4j_session,
        "AIBOMComponent",
        ["name"],
    )
    assert component_nodes is not None
    assert len(component_nodes) > 0

    assert check_rels(
        neo4j_session,
        "AIBOMSource",
        "source_key",
        "GitLabProject",
        "web_url",
        "SCANNED_REPOSITORY",
        rel_direction_right=True,
    ) == {
        (TEST_GITLAB_PROJECT_URL, TEST_GITLAB_PROJECT_URL),
    }

    detected_in_rels = check_rels(
        neo4j_session,
        "AIBOMComponent",
        "name",
        "GitLabProject",
        "web_url",
        "DETECTED_IN",
        rel_direction_right=True,
    )
    assert len(detected_in_rels) == len(component_nodes)
