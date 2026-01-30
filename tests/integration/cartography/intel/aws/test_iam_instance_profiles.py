from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.iam_instance_profiles
from cartography.intel.aws.ec2.instances import sync_ec2_instances
from cartography.intel.aws.iam import sync_role_assumptions
from cartography.intel.aws.iam_instance_profiles import sync_iam_instance_profiles
from cartography.util import run_scoped_analysis_job
from tests.data.aws.ec2.instances import INSTANCE_WITH_IAM_PROFILE
from tests.data.aws.iam.instance_profiles import INSTANCE_PROFILES
from tests.data.aws.iam.roles import ROLES
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "1234"
TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.aws.iam_instance_profiles,
    "get_iam_instance_profiles",
    return_value=INSTANCE_PROFILES,
)
@patch.object(
    cartography.intel.aws.iam, "get_role_list_data", return_value=ROLES["Roles"]
)
@patch.object(
    cartography.intel.aws.ec2.instances,
    "get_ec2_instances",
    return_value=INSTANCE_WITH_IAM_PROFILE,
)
def test_sync_iam_instance_profiles(
    mock_get_profiles, mock_get_roles, mock_get_instances, neo4j_session
):
    """
    Ensure that IAM instance profiles are properly ingested and connected to roles and EC2 instances
    """
    # Arrange
    boto3_session = MagicMock()
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID}
    sync_role_assumptions(
        neo4j_session,
        ROLES,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    # Act
    sync_iam_instance_profiles(
        boto3_session,
        neo4j_session,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        ["us-east-1"],
        common_job_parameters,
    )

    # Assert instance profile nodes exist
    assert check_nodes(
        neo4j_session, "AWSInstanceProfile", ["id", "instance_profile_name"]
    ) == {
        (
            "arn:aws:iam::1234:instance-profile/cartography-service",
            "cartography-service",
        ),
    }

    # Assert instance profile to AWS account relationship
    assert check_rels(
        neo4j_session,
        "AWSInstanceProfile",
        "id",
        "AWSAccount",
        "id",
        "RESOURCE",
        rel_direction_right=False,
    ) == {
        ("arn:aws:iam::1234:instance-profile/cartography-service", "1234"),
    }

    # Assert instance profile to role relationship
    assert check_rels(
        neo4j_session,
        "AWSInstanceProfile",
        "id",
        "AWSRole",
        "arn",
        "ASSOCIATED_WITH",
        rel_direction_right=True,
    ) == {
        (
            "arn:aws:iam::1234:instance-profile/cartography-service",
            "arn:aws:iam::1234:role/cartography-service",
        ),
    }

    # Arrange and act load EC2 instances
    sync_ec2_instances(
        neo4j_session,
        boto3_session,
        ["us-east-1"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    # Assert EC2 Instance to Instance Profile relationship
    assert check_rels(
        neo4j_session,
        "EC2Instance",
        "id",
        "AWSInstanceProfile",
        "arn",
        "INSTANCE_PROFILE",
        rel_direction_right=True,
    ) == {
        ("i-00bd", "arn:aws:iam::1234:instance-profile/cartography-service"),
    }

    # Act
    run_scoped_analysis_job(
        "aws_ec2_iaminstanceprofile.json",
        neo4j_session,
        common_job_parameters,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "EC2Instance",
        "id",
        "AWSRole",
        "arn",
        "STS_ASSUMEROLE_ALLOW",
        rel_direction_right=True,
    ) == {
        ("i-00bd", "arn:aws:iam::1234:role/cartography-service"),
    }
