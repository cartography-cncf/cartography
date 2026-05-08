from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.azure.functions as functions
from cartography.util import run_analysis_job
from tests.data.azure.functions import MOCK_FUNCTION_APP_CONFIGS
from tests.data.azure.functions import MOCK_FUNCTION_APPS
from tests.data.azure.functions import TEST_FUNCTIONAPP_CODE_ID
from tests.data.azure.functions import TEST_FUNCTIONAPP_CONTAINER_ID
from tests.data.azure.functions import TEST_FUNCTIONAPP_IMAGE_DIGEST
from tests.data.azure.functions import TEST_FUNCTIONAPP_IMAGE_URI
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_SUBSCRIPTION_ID = "00-00-00-00"
TEST_UPDATE_TAG = 123456789


@patch("cartography.intel.azure.functions.fetch_function_app_configurations")
@patch("cartography.intel.azure.functions.get_function_apps")
def test_sync_function_apps(mock_get, mock_fetch_configs, neo4j_session):
    """
    Test that we can correctly sync Azure Function App data and relationships.
    """
    # Arrange
    mock_get.return_value = MOCK_FUNCTION_APPS
    mock_fetch_configs.return_value = MOCK_FUNCTION_APP_CONFIGS

    # Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
    }

    # Act
    functions.sync(
        neo4j_session,
        MagicMock(),  # credentials object is not used directly by sync as get is mocked
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert Nodes: Both function apps (code + container kinds) are loaded; plain web app is filtered out.
    expected_nodes = {
        (TEST_FUNCTIONAPP_CODE_ID, "my-test-func-app"),
        (TEST_FUNCTIONAPP_CONTAINER_ID, "my-container-func-app"),
    }
    actual_nodes = check_nodes(neo4j_session, "AzureFunctionApp", ["id", "name"])
    assert actual_nodes == expected_nodes

    # Assert: container-based function app has image fields populated,
    # and the Function ontology sees deployment_type correctly ("container" vs "code").
    assert check_nodes(
        neo4j_session,
        "AzureFunctionApp",
        [
            "id",
            "is_container",
            "deployment_type",
            "image_uri",
            "image_digest",
            "architecture_normalized",
            "_ont_deployment_type",
        ],
    ) == {
        (TEST_FUNCTIONAPP_CODE_ID, False, "code", None, None, None, "code"),
        (
            TEST_FUNCTIONAPP_CONTAINER_ID,
            True,
            "container",
            TEST_FUNCTIONAPP_IMAGE_URI,
            TEST_FUNCTIONAPP_IMAGE_DIGEST,
            "amd64",
            "container",
        ),
    }

    # Assert Relationships
    expected_rels = {
        (TEST_SUBSCRIPTION_ID, TEST_FUNCTIONAPP_CODE_ID),
        (TEST_SUBSCRIPTION_ID, TEST_FUNCTIONAPP_CONTAINER_ID),
    }
    actual_rels = check_rels(
        neo4j_session,
        "AzureSubscription",
        "id",
        "AzureFunctionApp",
        "id",
        "RESOURCE",
    )
    assert actual_rels == expected_rels


@patch("cartography.intel.azure.functions.fetch_function_app_configurations")
@patch("cartography.intel.azure.functions.get_function_apps")
def test_container_function_app_has_image_and_resolved_image(
    mock_get, mock_fetch_configs, neo4j_session
):
    """A container-deployed Function App should get HAS_IMAGE to ECRImage
    (matched on digest) and a RESOLVED_IMAGE edge via the Function analysis pass."""
    mock_get.return_value = MOCK_FUNCTION_APPS
    mock_fetch_configs.return_value = MOCK_FUNCTION_APP_CONFIGS

    neo4j_session.run(
        "MERGE (s:AzureSubscription{id: $sub_id}) SET s.lastupdated = $tag",
        sub_id=TEST_SUBSCRIPTION_ID,
        tag=TEST_UPDATE_TAG,
    )
    neo4j_session.run(
        """
        MERGE (i:Image:ECRImage {id: $digest})
        SET i.digest = $digest, i.lastupdated = $tag
        """,
        digest=TEST_FUNCTIONAPP_IMAGE_DIGEST,
        tag=TEST_UPDATE_TAG,
    )

    functions.sync(
        neo4j_session,
        MagicMock(),
        TEST_SUBSCRIPTION_ID,
        TEST_UPDATE_TAG,
        {
            "UPDATE_TAG": TEST_UPDATE_TAG,
            "AZURE_SUBSCRIPTION_ID": TEST_SUBSCRIPTION_ID,
        },
    )

    assert check_rels(
        neo4j_session,
        "AzureFunctionApp",
        "id",
        "ECRImage",
        "digest",
        "HAS_IMAGE",
    ) == {(TEST_FUNCTIONAPP_CONTAINER_ID, TEST_FUNCTIONAPP_IMAGE_DIGEST)}

    run_analysis_job(
        "resolved_image_analysis.json",
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    assert check_rels(
        neo4j_session,
        "Function",
        "id",
        "Image",
        "id",
        "RESOLVED_IMAGE",
    ) == {(TEST_FUNCTIONAPP_CONTAINER_ID, TEST_FUNCTIONAPP_IMAGE_DIGEST)}


def test_load_function_app_tags(neo4j_session):
    """
    Test that tags are correctly loaded and linked to Azure Function Apps.
    """
    # 1. Arrange: Create the prerequisite AzureSubscription node
    neo4j_session.run(
        """
        MERGE (s:AzureSubscription{id: $sub_id})
        SET s.lastupdated = $update_tag
        """,
        sub_id=TEST_SUBSCRIPTION_ID,
        update_tag=TEST_UPDATE_TAG,
    )

    transformed_apps = functions.transform_function_apps(MOCK_FUNCTION_APPS)

    # Load the function apps so the parent node exists
    functions.load_function_apps(
        neo4j_session, transformed_apps, TEST_SUBSCRIPTION_ID, TEST_UPDATE_TAG
    )

    # 2. Act: Load the tags
    functions.load_function_app_tags(
        neo4j_session,
        TEST_SUBSCRIPTION_ID,
        transformed_apps,
        TEST_UPDATE_TAG,
    )

    # 3. Assert: Check that the AzureTag nodes exist
    expected_tags = {
        f"{TEST_SUBSCRIPTION_ID}|env:prod",
        f"{TEST_SUBSCRIPTION_ID}|service:function-app",
    }
    tag_nodes = neo4j_session.run("MATCH (t:AzureTag) RETURN t.id")
    actual_tags = {n["t.id"] for n in tag_nodes}
    assert actual_tags == expected_tags

    # 4. Assert: Both function apps (code + container) carry the same shared tags.
    expected_rels = {
        (TEST_FUNCTIONAPP_CODE_ID, f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (TEST_FUNCTIONAPP_CODE_ID, f"{TEST_SUBSCRIPTION_ID}|service:function-app"),
        (TEST_FUNCTIONAPP_CONTAINER_ID, f"{TEST_SUBSCRIPTION_ID}|env:prod"),
        (TEST_FUNCTIONAPP_CONTAINER_ID, f"{TEST_SUBSCRIPTION_ID}|service:function-app"),
    }

    result = neo4j_session.run(
        """
        MATCH (fa:AzureFunctionApp)-[:TAGGED]->(t:AzureTag)
        RETURN fa.id, t.id
        """
    )
    actual_rels = {(r["fa.id"], r["t.id"]) for r in result}
    assert actual_rels == expected_rels
