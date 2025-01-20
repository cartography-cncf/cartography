from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.inspector
from cartography.intel.aws.inspector import sync
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456
TEST_REGION = 'us-west-2'
TEST_ACC_ID_1 = '123456789011'
TEST_ACC_ID_2 = '123456789012'


@patch.object(cartography.intel.aws.inspector, 'get_inspector_findings', return_value=LIST_FINDINGS_NETWORK)
def test_sync_inspector_network_findings(mock_get, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )
    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:EC2Instance{id: 'i-instanceid', instanceid: 'i-instanceid'})
        """,
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACC_ID_1,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACC_ID_1},
    )

    # Assert Finding to EC2Instance exists
    assert check_rels(
        neo4j_session,
        'AWSInspectorFinding',
        'id',
        'EC2Instance',
        'id',
        'AFFECTS',
        rel_direction_right=True,
    ) == {
        ('arn:aws:test123', 'i-instanceid'),
    }

    # Assert AWSAccount to Finding exists
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'AWSInspectorFinding',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        ('123456789011', 'arn:aws:test123'),
    }


@patch.object(cartography.intel.aws.inspector, 'get_inspector_findings', return_value=LIST_FINDINGS_EC2_PACKAGE)
def test_sync_inspector_ec2_package_findings(mock_get, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    # Remove everything previously put in the test graph since the fixture scope is set to module and not function.
    neo4j_session.run(
        """
        MATCH (n) DETACH DELETE n;
        """,
    )
    # Add some fake accounts
    neo4j_session.run(
        """
        MERGE (:AWSAccount{id: '123456789012'})
        MERGE (:AWSAccount{id: '123456789011'})
        """,
    )
    # Add some fake instances
    neo4j_session.run(
        """
        MERGE (:EC2Instance{id: 'i-88503981029833100', instanceid: 'i-88503981029833100'})
        MERGE (:EC2Instance{id: 'i-88503981029833101', instanceid: 'i-88503981029833101'})
        """,
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACC_ID_2,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACC_ID_2},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        'AWSInspectorFinding',
        'id',
        'EC2Instance',
        'id',
        'AFFECTS',
        rel_direction_right=True,
    ) == {
        ('arn:aws:test456', 'i-88503981029833100'),
        ('arn:aws:test789', 'i-88503981029833101'),
    }

    assert check_rels(
        neo4j_session,
        'AWSInspectorFinding',
        'id',
        'AWSInspectorPackage',
        'id',
        'HAS',
        rel_direction_right=True,
    ) == {
        ('arn:aws:test456', 'kernel-tools|X86_64|4.9.17|6.29.amzn1|0'),
        ('arn:aws:test456', 'kernel|X86_64|4.9.17|6.29.amzn1|0'),
        ('arn:aws:test789', 'openssl|X86_64|1.0.2k|1.amzn2|0'),
    }

    # Assert AWSAccount RESOURCE to Finding exists
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'AWSInspectorFinding',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        ('123456789012', 'arn:aws:test456'),
        ('123456789012', 'arn:aws:test789'),
    }

    # Assert AWSAccount MEMBER to Finding exists
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'AWSInspectorFinding',
        'id',
        'MEMBER',
        rel_direction_right=True,
    ) == {
        ('123456789011', 'arn:aws:test789'),
        ('123456789012', 'arn:aws:test456'),
    }
