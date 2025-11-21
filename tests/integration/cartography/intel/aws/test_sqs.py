from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.sqs
import tests.data.aws.sqs
from cartography.intel.aws.sqs import sync
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789


def test_load_sqs_queues(neo4j_session, *args):
    """
    Ensure that expected queues get loaded with their key fields.
    """
    raw_data = tests.data.aws.sqs.GET_SQS_QUEUE_ATTRIBUTES
    transformed = cartography.intel.aws.sqs.transform_sqs_queues(raw_data)
    cartography.intel.aws.sqs.load_sqs_queues(
        neo4j_session,
        transformed,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    expected_nodes = {
        (
            "test-queue-1",
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-1",
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-1",
            1627539901900,
            1627539901900,
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",
            "1",
            "10",
        ),
        (
            "test-queue-2",
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",
            1627539901900,
            1627539901900,
            None,
            None,
            "10",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (q:SQSQueue)
        RETURN q.name, q.id, q.arn, q.created_timestamp, q.last_modified_timestamp,
        q.redrive_policy_dead_letter_target_arn, q.redrive_policy_max_receive_count,
        q.visibility_timeout
        """,
    )
    actual_nodes = {
        (
            n["q.name"],
            n["q.id"],
            n["q.arn"],
            n["q.created_timestamp"],
            n["q.last_modified_timestamp"],
            n["q.redrive_policy_dead_letter_target_arn"],
            n["q.redrive_policy_max_receive_count"],
            n["q.visibility_timeout"],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes

    expected_relationship = {
        (
            "test-queue-1",
            "test-queue-2",
        ),
    }
    relation = neo4j_session.run(
        """
        MATCH (q1:SQSQueue)-[:HAS_DEADLETTER_QUEUE]->(q2:SQSQueue)
        RETURN q1.name, q2.name
        """,
    )
    actual_relationship = {
        (
            r["q1.name"],
            r["q2.name"],
        )
        for r in relation
    }
    assert actual_relationship == expected_relationship


@patch.object(
    cartography.intel.aws.sqs,
    "get_sqs_queue_list",
    return_value=[url for url, _ in tests.data.aws.sqs.GET_SQS_QUEUE_ATTRIBUTES],
)
@patch.object(
    cartography.intel.aws.sqs,
    "get_sqs_queue_attributes",
    return_value=tests.data.aws.sqs.GET_SQS_QUEUE_ATTRIBUTES,
)
def test_sync_sqs(mock_get_attrs, mock_get_list, neo4j_session):
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "SQSQueue",
        ["arn"],
    ) == {
        ("arn:aws:secretsmanager:us-east-1:000000000000:test-queue-1",),
        ("arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",),
    }

    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "SQSQueue",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-1",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",
        ),
    }

    assert check_rels(
        neo4j_session,
        "SQSQueue",
        "arn",
        "SQSQueue",
        "arn",
        "HAS_DEADLETTER_QUEUE",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-1",
            "arn:aws:secretsmanager:us-east-1:000000000000:test-queue-2",
        ),
    }
