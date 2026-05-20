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
from tests.data.aibom.aibom_sample import TEST_SOURCE_KEY
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789
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
