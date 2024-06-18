from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2.instances
import cartography.intel.aws.iam
import tests.data.aws.ec2.instances
import tests.data.aws.iam
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.util import run_analysis_job
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
def test_sync_ec2_instances(mock_get_instances, neo4j_session):
    """
    Ensure that instances actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Act
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert EC2 instances exist
    assert check_nodes(neo4j_session, 'EC2Instance', ['id', 'instanceid']) == {
        ("i-01", "i-01"),
        ("i-02", "i-02"),
        ("i-03", "i-03"),
        ("i-04", "i-04"),
    }

    # Assert that instances are connected to their expected reservations
    assert check_rels(
        neo4j_session,
        'EC2Reservation',
        'reservationid',
        'EC2Instance',
        'id',
        'MEMBER_OF_EC2_RESERVATION',
        rel_direction_right=False,
    ) == {
        ("r-01", "i-01"),
        ("r-02", "i-02"),
        ("r-03", "i-03"),
        ("r-03", "i-04"),
    }

    # Assert network interface to instances
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'EC2Instance',
        'id',
        'NETWORK_INTERFACE',
        rel_direction_right=False,
    ) == {
        ('eni-de', 'i-01'),
        ('eni-87', 'i-02'),
        ('eni-75', 'i-03'),
        ('eni-76', 'i-04'),
    }

    # Assert network interface to subnet
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'EC2Subnet',
        'id',
        'PART_OF_SUBNET',
        rel_direction_right=True,
    ) == {
        ('eni-75', 'SOME_SUBNET_1'),
        ('eni-76', 'SOME_SUBNET_1'),
        ('eni-87', 'SOME_SUBNET_1'),
    }

    # #1316: Assert the fields of the subnet are as expected and that subnet_id does not exist
    assert check_nodes(neo4j_session, 'EC2Subnet', ['id', 'subnetid', 'subnet_id']) == {
        ('SOME_SUBNET_1', 'SOME_SUBNET_1', None),
    }

    # Assert network interface to security group
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'EC2SecurityGroup',
        'id',
        'MEMBER_OF_EC2_SECURITY_GROUP',
        rel_direction_right=True,
    ) == {
        ('eni-75', 'SOME_GROUP_ID_2'),
        ('eni-75', 'THIS_IS_A_SG_ID'),
        ('eni-76', 'SOME_GROUP_ID_2'),
        ('eni-76', 'THIS_IS_A_SG_ID'),
        ('eni-87', 'SOME_GROUP_ID_2'),
        ('eni-87', 'SOME_GROUP_ID_3'),
        ('eni-de', 'SOME_GROUP_ID_2'),
        ('eni-de', 'sg-GROUP-ID'),
    }

    # Assert network interface to AWS account
    assert check_rels(
        neo4j_session,
        'NetworkInterface',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('eni-75', '000000000000'),
        ('eni-76', '000000000000'),
        ('eni-87', '000000000000'),
        ('eni-de', '000000000000'),
    }

    # Assert EC2 Key Pair to AWS account
    assert check_rels(
        neo4j_session,
        'EC2KeyPair',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('arn:aws:ec2:us-east-1:000000000000:key-pair/boot', '000000000000'),
    }

    # Assert EC2 Key Pair to EC2 instance
    assert check_rels(
        neo4j_session,
        'EC2KeyPair',
        'id',
        'EC2Instance',
        'id',
        'SSH_LOGIN_TO',
        rel_direction_right=True,
    ) == {
        ('arn:aws:ec2:us-east-1:000000000000:key-pair/boot', 'i-01'),
        ('arn:aws:ec2:us-east-1:000000000000:key-pair/boot', 'i-02'),
        ('arn:aws:ec2:us-east-1:000000000000:key-pair/boot', 'i-03'),
        ('arn:aws:ec2:us-east-1:000000000000:key-pair/boot', 'i-04'),
    }

    # Assert EC2 Security Group to EC2 Instance
    assert check_rels(
        neo4j_session,
        'EC2SecurityGroup',
        'id',
        'EC2Instance',
        'id',
        'MEMBER_OF_EC2_SECURITY_GROUP',
        rel_direction_right=False,
    ) == {
        ('sg-GROUP-ID', 'i-01'),
        ('SOME_GROUP_ID_2', 'i-01'),
        ('SOME_GROUP_ID_2', 'i-02'),
        ('SOME_GROUP_ID_2', 'i-03'),
        ('SOME_GROUP_ID_2', 'i-04'),
        ('SOME_GROUP_ID_3', 'i-02'),
        ('THIS_IS_A_SG_ID', 'i-03'),
        ('THIS_IS_A_SG_ID', 'i-04'),
    }

    # Assert EC2 Security Group to AWS account
    assert check_rels(
        neo4j_session,
        'EC2SecurityGroup',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('SOME_GROUP_ID_2', '000000000000'),
        ('SOME_GROUP_ID_3', '000000000000'),
        ('THIS_IS_A_SG_ID', '000000000000'),
        ('sg-GROUP-ID', '000000000000'),
    }

    # Assert EC2 Subnet to EC2 Instance
    assert check_rels(
        neo4j_session,
        'EC2Subnet',
        'id',
        'EC2Instance',
        'id',
        'PART_OF_SUBNET',
        rel_direction_right=False,
    ) == {
        ('SOME_SUBNET_1', 'i-02'),
        ('SOME_SUBNET_1', 'i-03'),
        ('SOME_SUBNET_1', 'i-04'),
    }

    # Assert EC2 Subnet to AWS account
    assert check_rels(
        neo4j_session,
        'EC2Subnet',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('SOME_SUBNET_1', '000000000000'),
    }

    # Assert EBS Volume to EC2 Instance
    assert check_rels(
        neo4j_session,
        'EBSVolume',
        'id',
        'EC2Instance',
        'id',
        'ATTACHED_TO',
        rel_direction_right=True,
    ) == {
        ('vol-0df', 'i-01'),
        ('vol-03', 'i-02'),
        ('vol-09', 'i-03'),
        ('vol-04', 'i-04'),
    }

    # Assert EBS Volume to AWS account
    assert check_rels(
        neo4j_session,
        'EBSVolume',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('vol-03', '000000000000'),
        ('vol-04', '000000000000'),
        ('vol-09', '000000000000'),
        ('vol-0df', '000000000000'),
    }


@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
def test_ec2_iaminstanceprofiles(mock_get_instances, neo4j_session):
    """
    Ensure that EC2Instances are attached to the IAM Roles that they can assume due to their IAM instance profiles
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    data_iam = tests.data.aws.iam.INSTACE['Roles']
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )
    cartography.intel.aws.iam.load_roles(
        neo4j_session, data_iam, TEST_ACCOUNT_ID, TEST_UPDATE_TAG,
    )
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
    }

    # Act
    run_analysis_job(
        'aws_ec2_iaminstanceprofile.json',
        neo4j_session,
        common_job_parameters,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        'EC2Instance',
        'id',
        'AWSRole',
        'arn',
        'STS_ASSUMEROLE_ALLOW',
        rel_direction_right=True,
    ) == {
        ('i-02', 'arn:aws:iam::000000000000:role/SERVICE_NAME_2'),
        ('i-03', 'arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME'),
        ('i-04', 'arn:aws:iam::000000000000:role/ANOTHER_SERVICE_NAME'),
    }
