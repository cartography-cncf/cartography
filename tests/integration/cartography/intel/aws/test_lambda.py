from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.lambda_function
import tests.data.aws.lambda_function
from tests.data.aws.lambda_function import mock_get_event_source_mappings_for_sync_test
from tests.data.aws.lambda_function import mock_get_function_aliases_for_sync_test
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.lambda_function,
    "get_lambda_permissions",
    return_value=tests.data.aws.lambda_function.LIST_LAMBDA_PERMISSIONS,
)
@patch.object(
    cartography.intel.aws.lambda_function,
    "get_lambda_data",
    return_value=tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS,
)
@patch.object(
    cartography.intel.aws.lambda_function,
    "get_function_aliases",
    side_effect=mock_get_function_aliases_for_sync_test,
)
@patch.object(
    cartography.intel.aws.lambda_function,
    "get_event_source_mappings",
    side_effect=mock_get_event_source_mappings_for_sync_test,
)
def test_sync_lambda_functions(
    mock_get_event_source_mappings,
    mock_get_function_aliases,
    mock_get_event_source_data,
    mock_get_lambda_permissions,
    neo4j_session,
):
    """
    Test that the complete Lambda sync function works end-to-end with mocked get functions.
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID}

    # Act
    cartography.intel.aws.lambda_function.sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert - Check all node types were created correctly

    assert check_nodes(neo4j_session, "AWSLambda", ["id", "anonymous_access"]) == {
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",
            False,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
            True,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
            None,
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
            None,
        ),
    }

    assert check_nodes(neo4j_session, "AWSLambdaFunctionAlias", ["id"]) == {
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",),
    }

    assert check_nodes(neo4j_session, "AWSLambdaEventSourceMapping", ["id"]) == {
        ("i01",),
        ("i02",),
    }

    assert check_nodes(neo4j_session, "AWSLambdaLayer", ["id"]) == {
        ("arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",),
        ("arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",),
        ("arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",),
    }

    # Assert - Check all relationship types were created correctly

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambda",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambdaFunctionAlias",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambdaEventSourceMapping",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "i01"),
        (TEST_ACCOUNT_ID, "i02"),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambdaLayer",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1"),
        (TEST_ACCOUNT_ID, "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2"),
        (TEST_ACCOUNT_ID, "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3"),
    }

    assert check_rels(
        neo4j_session,
        "AWSLambda",
        "id",
        "AWSLambdaFunctionAlias",
        "id",
        "KNOWN_AS",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",
        ),
    }

    assert check_rels(
        neo4j_session,
        "AWSLambda",
        "id",
        "AWSLambdaEventSourceMapping",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-7", "i01"),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-8", "i02"),
    }

    assert check_rels(
        neo4j_session,
        "AWSLambda",
        "id",
        "AWSLambdaLayer",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
            "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
            "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
            "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",
        ),
    }


def test_load_lambda_functions(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    permissions = tests.data.aws.lambda_function.LIST_LAMBDA_PERMISSIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
        permissions,
        TEST_REGION,
    )

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test Lambda nodes were created correctly
    assert check_nodes(neo4j_session, "AWSLambda", ["id"]) == {
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",),
    }


def test_load_lambda_relationships(neo4j_session):
    # Create Test AWSAccount
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Load Test Lambda Functions
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    permissions = tests.data.aws.lambda_function.LIST_LAMBDA_PERMISSIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
        permissions,
        TEST_REGION,
    )

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test AWSAccount -> AWSLambda RESOURCE relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambda",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
        ),
    }


def test_load_lambda_function_aliases(neo4j_session):
    # Create Test AWSAccount first for sub-resource relationships
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTION_ALIASES

    cartography.intel.aws.lambda_function.load_lambda_function_aliases(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test Lambda alias nodes were created correctly
    assert check_nodes(neo4j_session, "AWSLambdaFunctionAlias", ["id"]) == {
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",),
    }

    # Test AWSAccount -> AWSLambdaFunctionAlias RESOURCE relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambdaFunctionAlias",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",
        ),
    }


def test_load_lambda_function_aliases_relationships(neo4j_session):
    # Create Test AWSAccount first
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    permissions = tests.data.aws.lambda_function.LIST_LAMBDA_PERMISSIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
        permissions,
        TEST_REGION,
    )

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    aliases = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTION_ALIASES

    cartography.intel.aws.lambda_function.load_lambda_function_aliases(
        neo4j_session,
        aliases,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test AWSLambda -> AWSLambdaFunctionAlias KNOWN_AS relationships
    assert check_rels(
        neo4j_session,
        "AWSLambda",
        "id",
        "AWSLambdaFunctionAlias",
        "id",
        "KNOWN_AS",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",
        ),
    }


def test_load_lambda_event_source_mappings(neo4j_session):
    # Create Test AWSAccount first for sub-resource relationships
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data = tests.data.aws.lambda_function.LIST_EVENT_SOURCE_MAPPINGS

    cartography.intel.aws.lambda_function.load_lambda_event_source_mappings(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test Lambda event source mapping nodes were created correctly
    assert check_nodes(neo4j_session, "AWSLambdaEventSourceMapping", ["id"]) == {
        ("i01",),
        ("i02",),
    }

    # Test AWSAccount -> AWSLambdaEventSourceMapping RESOURCE relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambdaEventSourceMapping",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "i01"),
        (TEST_ACCOUNT_ID, "i02"),
    }


def test_load_lambda_event_source_mappings_relationships(neo4j_session):
    # Create Test AWSAccount first
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    permissions = tests.data.aws.lambda_function.LIST_LAMBDA_PERMISSIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
        permissions,
        TEST_REGION,
    )

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    esm = tests.data.aws.lambda_function.LIST_EVENT_SOURCE_MAPPINGS

    cartography.intel.aws.lambda_function.load_lambda_event_source_mappings(
        neo4j_session,
        esm,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test AWSLambda -> AWSLambdaEventSourceMapping RESOURCE relationships
    assert check_rels(
        neo4j_session,
        "AWSLambda",
        "id",
        "AWSLambdaEventSourceMapping",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-7", "i01"),
        ("arn:aws:lambda:us-west-2:000000000000:function:sample-function-8", "i02"),
    }


def test_load_lambda_layers(neo4j_session):
    # Create Test AWSAccount first for sub-resource relationships
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    data = tests.data.aws.lambda_function.LIST_LAYERS

    cartography.intel.aws.lambda_function.load_lambda_layers(
        neo4j_session,
        data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test Lambda layer nodes were created correctly
    assert check_nodes(neo4j_session, "AWSLambdaLayer", ["id"]) == {
        ("arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",),
        ("arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",),
        ("arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",),
    }

    # Test AWSAccount -> AWSLambdaLayer RESOURCE relationships
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSLambdaLayer",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1"),
        (TEST_ACCOUNT_ID, "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2"),
        (TEST_ACCOUNT_ID, "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3"),
    }


def test_load_lambda_layers_relationships(neo4j_session):
    # Create Test AWSAccount first
    neo4j_session.run(
        """
        MERGE (aws:AWSAccount{id: $aws_account_id})
        ON CREATE SET aws.firstseen = timestamp()
        SET aws.lastupdated = $aws_update_tag
        """,
        aws_account_id=TEST_ACCOUNT_ID,
        aws_update_tag=TEST_UPDATE_TAG,
    )

    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS
    permissions = tests.data.aws.lambda_function.LIST_LAMBDA_PERMISSIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
        permissions,
        TEST_REGION,
    )

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        transformed_data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    layers = tests.data.aws.lambda_function.LIST_LAYERS

    cartography.intel.aws.lambda_function.load_lambda_layers(
        neo4j_session,
        layers,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Test AWSLambda -> AWSLambdaLayer HAS relationships
    assert check_rels(
        neo4j_session,
        "AWSLambda",
        "id",
        "AWSLambdaLayer",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
            "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
            "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
            "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",
        ),
    }
