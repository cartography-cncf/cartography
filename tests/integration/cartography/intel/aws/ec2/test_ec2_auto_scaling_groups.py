from unittest.mock import MagicMock
from unittest.mock import patch

from cartography.intel.aws.ec2 import auto_scaling_groups
from cartography.intel.aws.ec2 import instances
from cartography.intel.aws.ec2.auto_scaling_groups import sync_ec2_auto_scaling_groups
from tests.data.aws.ec2.auto_scaling_groups import GET_AUTO_SCALING_GROUPS
from tests.data.aws.ec2.auto_scaling_groups import GET_LAUNCH_CONFIGURATIONS
from tests.data.aws.ec2.instances import DESCRIBE_INSTANCES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels


TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789


@patch.object(auto_scaling_groups, 'get_ec2_auto_scaling_groups', return_value=GET_AUTO_SCALING_GROUPS)
@patch.object(auto_scaling_groups, 'get_launch_configurations', return_value=GET_LAUNCH_CONFIGURATIONS)
@patch.object(instances, 'get_ec2_instances', return_value=DESCRIBE_INSTANCES['Reservations'])
def test_sync_ec2_auto_scaling_groups(mock_get_instances, mock_get_launch_configs, mock_get_asgs, neo4j_session):
    """
    Ensure that auto scaling groups actually get loaded and have their key fields
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    # Ensure there are instances in the graph
    instances.sync_ec2_instances(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Act
    sync_ec2_auto_scaling_groups(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {'UPDATE_TAG': TEST_UPDATE_TAG, 'AWS_ID': TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, 'AutoScalingGroup', ['arn', 'name']) == {
        (GET_AUTO_SCALING_GROUPS[0]['AutoScalingGroupARN'], GET_AUTO_SCALING_GROUPS[0]['AutoScalingGroupName']),
        (GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupARN'], GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupName']),
    }

    assert check_nodes(neo4j_session, 'LaunchConfiguration', ['id', 'arn', 'name']) == {
        (
            GET_LAUNCH_CONFIGURATIONS[0]['LaunchConfigurationARN'],
            GET_LAUNCH_CONFIGURATIONS[0]['LaunchConfigurationARN'],
            GET_LAUNCH_CONFIGURATIONS[0]['LaunchConfigurationName'],
        ),
        (
            GET_LAUNCH_CONFIGURATIONS[1]['LaunchConfigurationARN'],
            GET_LAUNCH_CONFIGURATIONS[1]['LaunchConfigurationARN'],
            GET_LAUNCH_CONFIGURATIONS[1]['LaunchConfigurationName'],
        ),
        (
            GET_LAUNCH_CONFIGURATIONS[2]['LaunchConfigurationARN'],
            GET_LAUNCH_CONFIGURATIONS[2]['LaunchConfigurationARN'],
            GET_LAUNCH_CONFIGURATIONS[2]['LaunchConfigurationName'],
        ),
    }

    assert check_rels(
        neo4j_session,
        node_1_label='AutoScalingGroup',
        node_1_attr='id',
        node_2_label='AWSAccount',
        node_2_attr='id',
        rel_label='RESOURCE',
        rel_direction_right=False,
    ) == {
        (GET_AUTO_SCALING_GROUPS[0]['AutoScalingGroupARN'], TEST_ACCOUNT_ID),
        (GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupARN'], TEST_ACCOUNT_ID),
    }

    assert check_rels(
        neo4j_session,
        node_1_label='AutoScalingGroup',
        node_1_attr='id',
        node_2_label='LaunchConfiguration',
        node_2_attr='name',
        rel_label='HAS_LAUNCH_CONFIG',
        rel_direction_right=True,
    ) == {
        (GET_AUTO_SCALING_GROUPS[0]['AutoScalingGroupARN'], GET_LAUNCH_CONFIGURATIONS[0]['LaunchConfigurationName']),
    }

    assert check_rels(
        neo4j_session,
        node_1_label='AutoScalingGroup',
        node_1_attr='id',
        node_2_label='EC2Instance',
        node_2_attr='id',
        rel_label='MEMBER_AUTO_SCALE_GROUP',
        rel_direction_right=False,
    ) == {
        (GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupARN'], "i-01"),
        (GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupARN'], "i-02"),
        (GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupARN'], "i-03"),
        (GET_AUTO_SCALING_GROUPS[1]['AutoScalingGroupARN'], "i-04"),
    }
