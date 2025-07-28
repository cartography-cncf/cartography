import cartography.intel.aws.lambda_function
import tests.data.aws.lambda_function
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789


def test_load_lambda_functions(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
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

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
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
    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
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
    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
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
    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    # Transform the data first
    transformed_data = cartography.intel.aws.lambda_function.transform_lambda_functions(
        data,
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
