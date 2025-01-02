from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import tests.data.aws.ec2.key_pairs
from cartography.intel.aws.ec2.key_pairs import sync_ec2_key_pairs
from cartography.util import run_analysis_job


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.ec2.key_pairs,
    'get_ec2_key_pairs',
    return_value=tests.data.aws.ec2.key_pairs.DESCRIBE_KEY_PAIRS['KeyPairs'],
)
def test_sync_ec2_key_pairs(mock_key_pairs, neo4j_session):
    # Arrange
    boto3_session = MagicMock()

    # Act
    sync_ec2_key_pairs(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert
    expected_nodes = {
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_1",
            "11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11",
        ),
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_2",
            "22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22",
        ),
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_3",
            "33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33",
        ),
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_4",
            "44:44:44:44:44:44:44:44:44:44:44:44:44:44:44:44",
        ),
    }

    nodes = neo4j_session.run(
        """
        MATCH (k:EC2KeyPair) return k.arn, k.keyfingerprint
        """,
    )
    actual_nodes = {
        (
            n['k.arn'],
            n['k.keyfingerprint'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes


@patch.object(
    cartography.intel.aws.ec2.key_pairs,
    'get_ec2_key_pairs',
    return_value=tests.data.aws.ec2.key_pairs.DESCRIBE_KEY_PAIRS['KeyPairs'],
)
def test_ec2_key_pairs_analysis_job(mock_key_pairs, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    sync_ec2_key_pairs(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Act
    run_analysis_job(
        'aws_ec2_keypair_analysis.json',
        neo4j_session,
        {'UPDATE_TAG': TEST_UPDATE_TAG},
    )

    # Assert
    expected_nodes = {
        (
            "arn:aws:ec2:us-east-1:000000000000:key-pair/sample_key_pair_4",
            "44:44:44:44:44:44:44:44:44:44:44:44:44:44:44:44",
            True,
        ),
    }
    nodes = neo4j_session.run(
        """
        MATCH (k:EC2KeyPair) WHERE k.user_uploaded = true RETURN k.arn, k.keyfingerprint, k.user_uploaded
        """,
    )
    actual_nodes = {
        (
            n['k.arn'],
            n['k.keyfingerprint'],
            n['k.user_uploaded'],
        )
        for n in nodes
    }
    assert actual_nodes == expected_nodes
