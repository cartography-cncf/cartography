from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.dynamodb
import tests.data.aws.dynamodb
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.dynamodb, 'get_dynamodb_tables',
    return_value=tests.data.aws.dynamodb.LIST_DYNAMODB_TABLES['Tables'],
)
def test_load_dynamodb(mock_get_instances, neo4j_session):
    """
    Ensure that instances actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    cartography.intel.aws.dynamodb.sync_dynamodb_tables(
        neo4j_session,
        boto3_session,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert ddb table nodes exist
    assert check_nodes(neo4j_session, 'DynamoDBTable', ['id', 'rows']) == {
        ("arn:aws:dynamodb:us-east-1:000000000000:table/example-table", 1000000),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/sample-table", 1000000),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/model-table", 1000000),
        ("arn:aws:dynamodb:us-east-1:000000000000:table/basic-table", 1000000),
    }

    # Assert ddb gsi nodes exist
    assert check_nodes(neo4j_session, 'DynamoDBGlobalSecondaryIndex', ['id']) == {
        ('arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index',),
        ('arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index',),
        ('arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index',),
        ('arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index',),
        ('arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index',),
        ('arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index',),
        ('arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index',),
        ('arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index',),
    }

    # Assert AWSAccount -> DynamoDBTable
    assert check_rels(
        neo4j_session,
        'DynamoDBTable',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('arn:aws:dynamodb:us-east-1:000000000000:table/example-table', '000000000000'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/sample-table', '000000000000'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/model-table', '000000000000'),
        ('arn:aws:dynamodb:us-east-1:000000000000:table/basic-table', '000000000000'),
    }

    # Assert AWSAccount -> DynamoDBGlobalSecondaryIndex
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'DynamoDBGlobalSecondaryIndex',
        'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index',
        ),
        (
            '000000000000',
            'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index',
        ),
    }

    # Assert DynamoDBTable -> DynamoDBGlobalSecondaryIndex
    assert check_rels(
        neo4j_session,
        'DynamoDBTable',
        'id',
        'DynamoDBGlobalSecondaryIndex',
        'id',
        'GLOBAL_SECONDARY_INDEX',
        rel_direction_right=True,
    ) == {
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/example-table',
            'arn:aws:dynamodb:us-east-1:table/example-table/index/sample_1-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/example-table',
            'arn:aws:dynamodb:us-east-1:table/example-table/index/sample_2-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/model-table',
            'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_1-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/model-table',
            'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_2-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/model-table',
            'arn:aws:dynamodb:us-east-1:table/model-table/index/sample_3-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/sample-table',
            'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_1-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/sample-table',
            'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_2-index',
        ),
        (
            'arn:aws:dynamodb:us-east-1:000000000000:table/sample-table',
            'arn:aws:dynamodb:us-east-1:table/sample-table/index/sample_3-index',
        ),
    }

    # Arrange: load in an unrelated EC2 instance. This should not be affected by the EMR module's cleanup job.
    neo4j_session.run(
        '''
        MERGE (i:EC2Instance{id:1234, lastupdated: $lastupdated})<-[r:RESOURCE]-(:AWSAccount{id: $aws_account_id})
        SET r.lastupdated = $lastupdated
        ''',
        aws_account_id=TEST_ACCOUNT_ID,
        lastupdated=TEST_UPDATE_TAG,
    )

    # [Pre-test] Assert that the unrelated EC2 instance exists
    assert check_rels(neo4j_session, 'AWSAccount', 'id', 'EC2Instance', 'id', 'RESOURCE') == {
        (TEST_ACCOUNT_ID, 1234),
    }

    # Act: run the cleanup job
    common_job_parameters = {
        'UPDATE_TAG': TEST_UPDATE_TAG + 1,  # Simulate a new sync run finished so the old update tag is obsolete now
        'AWS_ID': TEST_ACCOUNT_ID,
        # Add in extra params that may have been added by other modules.
        # Expectation: These should not affect cleanup job execution.
        'permission_relationships_file': '/path/to/perm/rels/file',
        'OKTA_ORG_ID': 'my-org-id',
    }
    cartography.intel.aws.dynamodb.cleanup_dynamodb_tables(neo4j_session, common_job_parameters)

    # Assert: Expect no ddb nodes in the graph now
    assert check_nodes(neo4j_session, 'DynamoDBTable', ['id']) == set()
    assert check_nodes(neo4j_session, 'DynamoDBGlobalSecondaryIndex', ['id']) == set()
    # Assert: Expect that the unrelated EC2 instance was not touched by the cleanup job
    assert check_rels(neo4j_session, 'AWSAccount', 'id', 'EC2Instance', 'id', 'RESOURCE') == {
        (TEST_ACCOUNT_ID, 1234),
    }
