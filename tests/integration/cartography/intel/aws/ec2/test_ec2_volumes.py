from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.ec2.volumes
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.volumes import sync_ebs_volumes
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.data.aws.ec2.volumes import DESCRIBE_VOLUMES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'eu-west-1'
TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.aws.ec2.volumes, 'get_volumes', return_value=DESCRIBE_VOLUMES)
def test_sync_ebs_volumes(mock_get_vols, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_ebs_volumes(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, 'EBSVolume', ['arn']) == {
        ('arn:aws:ec2:eu-west-1:000000000000:volume/vol-03',),
        ('arn:aws:ec2:eu-west-1:000000000000:volume/vol-0df',),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'EBSVolume',
        'volumeid',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_ACCOUNT_ID, 'vol-03'),
        (TEST_ACCOUNT_ID, 'vol-0df'),
    }


@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
@patch.object(cartography.intel.aws.ec2.volumes, 'get_volumes', return_value=DESCRIBE_VOLUMES)
def test_sync_ebs_volumes_e2e(mock_get_vols, mock_get_instances, neo4j_session):
    # Arrange
    neo4j_session.run('MATCH (n) DETACH DELETE n;')
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act: sync_ec2_instances() loads attached ebs volumes
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert that deleteontermination is set by sync_ec2_instances. The encrypted property isn't returned by this API.
    assert check_nodes(neo4j_session, 'EBSVolume', ['id', 'deleteontermination', 'encrypted']) == {
        ('vol-03', True, None),
        ('vol-04', True, None),
        ('vol-09', True, None),
        ('vol-0df', True, None),
    }

    # Assert that they are attached to the instances
    assert check_rels(
        neo4j_session,
        'EC2Instance',
        'instanceid',
        'EBSVolume',
        'volumeid',
        'ATTACHED_TO',
        rel_direction_right=False,
    ) == {
        ('i-01', 'vol-0df'),
        ('i-02', 'vol-03'),
        ('i-03', 'vol-09'),
        ('i-04', 'vol-04'),
    }

    # Assert that we created the account to volume rels correctly
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'EBSVolume',
        'volumeid',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        ('000000000000', 'vol-03'),
        ('000000000000', 'vol-04'),
        ('000000000000', 'vol-09'),
        ('000000000000', 'vol-0df'),
    }

    # Act
    sync_ebs_volumes(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert that additional fields such as `encrypted` have been added by sync_ebs_volumes(), while
    # deleteontermination has not been overwritten with None by sync_ebs_volumes()
    assert check_nodes(neo4j_session, 'EBSVolume', ['id', 'deleteontermination', 'encrypted']) == {
        # Attached to the instances initially
        ('vol-04', True, None),
        ('vol-09', True, None),
        # Added by ebs sync
        ('vol-03', True, True),
        ('vol-0df', True, True),
    }

    # Assert that they are still attached to the instances
    assert check_rels(
        neo4j_session,
        'EC2Instance',
        'instanceid',
        'EBSVolume',
        'volumeid',
        'ATTACHED_TO',
        rel_direction_right=False,
    ) == {
        ('i-01', 'vol-0df'),
        ('i-02', 'vol-03'),
        ('i-03', 'vol-09'),
        ('i-04', 'vol-04'),
    }

    # Assert that the account to volume rels still exist
    assert check_rels(
        neo4j_session,
        'AWSAccount',
        'id',
        'EBSVolume',
        'volumeid',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        ('000000000000', 'vol-03'),
        ('000000000000', 'vol-04'),
        ('000000000000', 'vol-09'),
        ('000000000000', 'vol-0df'),
    }
