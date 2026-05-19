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
from cartography.intel.gcp.artifact_registry.artifact import load_docker_images
from tests.data.aibom.aibom_sample import AIBOM_REPORT
from tests.data.aibom.aibom_sample import TEST_GAR_IMAGE_DIGEST
from tests.data.aibom.aibom_sample import TEST_GAR_IMAGE_URI
from tests.data.aibom.aibom_sample import TEST_GAR_PROJECT_ID
from tests.data.aibom.aibom_sample import TEST_GAR_REPOSITORY_ID
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


def _seed_gar_single_platform_graph(neo4j_session) -> None:
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        MERGE (project:GCPProject {id: $project_id})
        SET project.lastupdated = $update_tag
        MERGE (repo:GCPArtifactRegistryRepository:ContainerRegistry {id: $repo_id})
        SET repo.name = 'docker-repo',
            repo.location = 'us-central1',
            repo.registry_uri = $registry_uri,
            repo.lastupdated = $update_tag
        MERGE (project)-[resource:RESOURCE]->(repo)
        SET resource.lastupdated = $update_tag
        """,
        project_id=TEST_GAR_PROJECT_ID,
        repo_id=TEST_GAR_REPOSITORY_ID,
        registry_uri=f"us-central1-docker.pkg.dev/{TEST_GAR_PROJECT_ID}/docker-repo",
        update_tag=TEST_UPDATE_TAG,
    )
    load_docker_images(
        neo4j_session,
        [
            {
                "id": TEST_GAR_IMAGE_URI,
                "name": f"my-app@{TEST_GAR_IMAGE_DIGEST}",
                "uri": TEST_GAR_IMAGE_URI,
                "digest": TEST_GAR_IMAGE_DIGEST,
                "tag": "latest",
                "tags": ["latest"],
                "resource_name": (
                    f"{TEST_GAR_REPOSITORY_ID}/dockerImages/my-app@{TEST_GAR_IMAGE_DIGEST}"
                ),
                "digest_uri": (
                    f"us-central1-docker.pkg.dev/{TEST_GAR_PROJECT_ID}/docker-repo/my-app"
                    f"@{TEST_GAR_IMAGE_DIGEST}"
                ),
                "image_size_bytes": "123",
                "media_type": "application/vnd.oci.image.manifest.v1+json",
                "upload_time": "2024-01-10T00:00:00Z",
                "build_time": "2024-01-10T00:00:00Z",
                "update_time": "2024-01-10T00:00:00Z",
                "repository_id": TEST_GAR_REPOSITORY_ID,
                "project_id": TEST_GAR_PROJECT_ID,
            },
        ],
        TEST_GAR_PROJECT_ID,
        TEST_UPDATE_TAG,
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
