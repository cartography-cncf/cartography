import cartography.intel.aws.lambda_function
import tests.data.aws.lambda_function

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-west-2"
TEST_UPDATE_TAG = 123456789


def test_load_lambda_functions(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-1",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-2",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-4",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-5",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-6",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AWSLambda) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


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

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
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

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSAccount)-[:RESOURCE]->(n2:AWSLambda) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected_nodes


def test_load_lambda_function_aliases(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTION_ALIASES

    cartography.intel.aws.lambda_function._load_lambda_function_aliases(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-3:LIVE",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-9:LIVE",
        "arn:aws:lambda:us-west-2:000000000000:function:sample-function-10:LIVE",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AWSLambdaFunctionAlias) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_lambda_function_aliases_relationships(neo4j_session):
    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    aliases = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTION_ALIASES

    cartography.intel.aws.lambda_function._load_lambda_function_aliases(
        neo4j_session,
        aliases,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
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

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSLambda)-[:KNOWN_AS]->(n2:AWSLambdaFunctionAlias) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected_nodes


def test_load_lambda_event_source_mappings(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_EVENT_SOURCE_MAPPINGS

    cartography.intel.aws.lambda_function._load_lambda_event_source_mappings(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "i01",
        "i02",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AWSLambdaEventSourceMapping) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_lambda_event_source_mappings_relationships(neo4j_session):
    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    esm = tests.data.aws.lambda_function.LIST_EVENT_SOURCE_MAPPINGS

    cartography.intel.aws.lambda_function._load_lambda_event_source_mappings(
        neo4j_session,
        esm,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-7",
            "i01",
        ),
        (
            "arn:aws:lambda:us-west-2:000000000000:function:sample-function-8",
            "i02",
        ),
    }

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSLambda)-[:RESOURCE]->(n2:AWSLambdaEventSourceMapping) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected_nodes


def test_load_lambda_layers(neo4j_session):
    data = tests.data.aws.lambda_function.LIST_LAYERS

    cartography.intel.aws.lambda_function._load_lambda_layers(
        neo4j_session,
        data,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-1",
        "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-2",
        "arn:aws:lambda:us-east-2:123456789012:layer:my-layer-3",
    }

    nodes = neo4j_session.run(
        """
        MATCH (r:AWSLambdaLayer) RETURN r.id;
        """,
    )

    actual_nodes = {n["r.id"] for n in nodes}

    assert actual_nodes == expected_nodes


def test_load_lambda_layers_relationships(neo4j_session):
    # Create Test Lambda Function
    data = tests.data.aws.lambda_function.LIST_LAMBDA_FUNCTIONS

    cartography.intel.aws.lambda_function.load_lambda_functions(
        neo4j_session,
        data,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    layers = tests.data.aws.lambda_function.LIST_LAYERS

    cartography.intel.aws.lambda_function._load_lambda_layers(
        neo4j_session,
        layers,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
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

    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:AWSLambda)-[:HAS]->(n2:AWSLambdaLayer) RETURN n1.id, n2.id;
        """,
    )
    actual = {(r["n1.id"], r["n2.id"]) for r in result}

    assert actual == expected_nodes
