import copy
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
import cartography.intel.aws.resourcegroupstaggingapi as rgta
import tests.data.aws.resourcegroupstaggingapi
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account


TEST_ACCOUNT_ID = '1234'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


def _ensure_local_neo4j_has_test_ec2_instance_data(neo4j_session):
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    boto3_session = MagicMock()
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )


@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
def test_transform_and_load_ec2_tags(mock_get_instances, neo4j_session):
    """
    Verify that (:EC2Instance)-[:TAGGED]->(:AWSTag) relationships work as expected.
    """
    # Arrange
    _ensure_local_neo4j_has_test_ec2_instance_data(neo4j_session)
    resource_type = 'ec2:instance'
    get_resources_response = copy.deepcopy(tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE)

    # Act
    rgta.transform_tags(get_resources_response, resource_type)
    rgta.load_tags(
        neo4j_session,
        get_resources_response,
        resource_type,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Assert
    expected = {
        ('i-01', 'TestKey:TestValue'),
    }
    # Fetch relationships
    result = neo4j_session.run(
        """
        MATCH (n1:EC2Instance)-[:TAGGED]->(n2:AWSTag) RETURN n1.id, n2.id;
        """,
    )
    actual = {
        (r['n1.id'], r['n2.id']) for r in result
    }
    assert actual == expected

    # Act: Test the cleanup removes old tags that are not attached to any resource
    new_update_tag = TEST_UPDATE_TAG + 1
    new_response = copy.deepcopy(tests.data.aws.resourcegroupstaggingapi.GET_RESOURCES_RESPONSE_UPDATED)
    rgta.transform_tags(new_response, resource_type)
    rgta.load_tags(
        neo4j_session,
        new_response,
        resource_type,
        TEST_REGION,
        TEST_ACCOUNT_ID,
        new_update_tag,
    )
    neo4j_session.run('MATCH (i:EC2Instance) DETACH DELETE (i) RETURN COUNT(*) as TotalCompleted')
    rgta.cleanup(neo4j_session, {'AWS_ID': TEST_ACCOUNT_ID, 'UPDATE_TAG': new_update_tag})

    # Assert
    expected = {
        ('TestKeyUpdated:TestValueUpdated'),
    }
    result = neo4j_session.run('MATCH (t:AWSTag) RETURN t.id')
    actual = {
        (r['t.id']) for r in result
    }
    assert actual == expected
