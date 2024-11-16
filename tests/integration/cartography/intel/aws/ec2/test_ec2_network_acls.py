from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.ec2
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.ec2.network_acls import sync_network_acls
from cartography.intel.aws.ec2.subnets import sync_subnets
from cartography.intel.aws.ec2.vpc import sync_vpc
from tests.data.aws.ec2.network_acls.instances import INSTANCES_FOR_ACL_TEST
from tests.data.aws.ec2.network_acls.network_acls import DESCRIBE_NETWORK_ACLS
from tests.data.aws.ec2.network_acls.subnets import DESCRIBE_SUBNETS_FOR_ACL_TEST
from tests.data.aws.ec2.network_acls.vpcs import DESCRIBE_VPCS_FOR_ACL_TEST
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = '000000000000'
TEST_REGION = 'us-east-1'
TEST_UPDATE_TAG = 123456789
common_job_parameters: dict[str, Any] = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "AWS_ID": TEST_ACCOUNT_ID,
}


@patch.object(cartography.intel.aws.ec2.network_acls, 'get_network_acl_data', return_value=DESCRIBE_NETWORK_ACLS)
@patch.object(cartography.intel.aws.ec2.subnets, 'get_subnet_data', return_value=DESCRIBE_SUBNETS_FOR_ACL_TEST)
@patch.object(cartography.intel.aws.ec2.vpc, 'get_ec2_vpcs', return_value=DESCRIBE_VPCS_FOR_ACL_TEST)
@patch.object(cartography.intel.aws.ec2.instances, 'get_ec2_instances', return_value=INSTANCES_FOR_ACL_TEST)
def test_sync_ec2_network_acls(
        mock_instances: MagicMock,
        mock_vpcs: MagicMock,
        mock_subnets: MagicMock,
        mock_acls: MagicMock,
        neo4j_session,
):
    regions = [TEST_REGION]
    boto3_session = MagicMock()

    # Arrange: load in instances, vpc, subnets for this test
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        regions,
        TEST_ACCOUNT_ID,
        common_job_parameters['UPDATE_TAG'],
        common_job_parameters,
    )
    sync_vpc(
        neo4j_session,
        boto3_session,
        regions,
        TEST_ACCOUNT_ID,
        common_job_parameters['UPDATE_TAG'],
        common_job_parameters,
    )
    sync_subnets(
        neo4j_session,
        boto3_session,
        regions,
        TEST_ACCOUNT_ID,
        common_job_parameters['UPDATE_TAG'],
        common_job_parameters,
    )

    # Act
    sync_network_acls(
        neo4j_session,
        boto3_session,
        regions,
        TEST_ACCOUNT_ID,
        common_job_parameters['UPDATE_TAG'],
        common_job_parameters,
    )

    # Assert that ACLs are connected to their expected rules
    assert check_rels(
        neo4j_session,
        'EC2NetworkAcl',
        'network_acl_id',
        'EC2NetworkAclRule',
        'id',
        'MEMBER_OF_NACL',
        rel_direction_right=False,
    ) == {
        ('acl-077e', 'acl-077e/egress/100'),
        ('acl-077e', 'acl-077e/egress/32767'),
        ('acl-077e', 'acl-077e/inbound/100'),
        ('acl-077e', 'acl-077e/inbound/32767'),
    }

    # Assert that ACL is attached to expected subnet
    assert check_rels(
        neo4j_session,
        'EC2NetworkAcl',
        'network_acl_id',
        'EC2Subnet',
        'subnetid',
        'PART_OF_SUBNET',
        rel_direction_right=True,
    ) == {
        ('acl-077e', 'subnet-06ba'),
    }

    # Assert that ACL is attached to account
    assert check_rels(
        neo4j_session,
        'EC2NetworkAcl',
        'network_acl_id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('acl-077e', '000000000000'),
    }

# Assert that ACL rule is attached to account
    assert check_rels(
        neo4j_session,
        'EC2NetworkAclRule',
        'id',
        'AWSAccount',
        'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('acl-077e/egress/100', '000000000000'),
        ('acl-077e/egress/32767', '000000000000'),
        ('acl-077e/inbound/100', '000000000000'),
        ('acl-077e/inbound/32767', '000000000000'),
    }
