from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.aws.iam
import cartography.intel.aws.permission_relationships
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "us-east-1"
TEST_UPDATE_TAG = 123456789

# Test data: a simple IAM role with a policy that allows S3 read access
SIMPLE_ROLE_DATA = {
    "Roles": [
        {
            "Path": "/",
            "RoleName": "TestReadRole",
            "RoleId": "AROABC123DEFGHIJKLMN",
            "Arn": "arn:aws:iam::000000000000:role/TestReadRole",
            "CreateDate": "2023-01-01T00:00:00+00:00",
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::000000000000:root"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            },
        }
    ]
}

# Mock policy data that grants S3 read access
ROLE_POLICY_DATA = {
    "arn:aws:iam::000000000000:role/TestReadRole": {
        "S3ReadPolicy": [
            {
                "Effect": "Allow",
                "Action": ["s3:GetObject"],
                "Resource": ["arn:aws:s3:::test-bucket*"],
            }
        ]
    }
}


def test_permission_relationships_with_iam_integration(neo4j_session):
    """
    Integration test that reproduces issue #1918.
    """
    # Arrange
    # Step 1: Create AWS account
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)

    # Step 2: Create S3 bucket resource (out of band to be quick and dirty)
    neo4j_session.run(
        """
        MATCH (aws:AWSAccount{id: $AccountId})
        MERGE (s3:S3Bucket{arn: 'arn:aws:s3:::test-bucket'})<-[:RESOURCE]-(aws)
        SET s3.lastupdated = $UpdateTag
        """,
        AccountId=TEST_ACCOUNT_ID,
        UpdateTag=TEST_UPDATE_TAG,
    )

    # Step 3: Create IAM roles and policies using sync_roles
    with (
        patch(
            "cartography.intel.aws.iam.get_role_list_data",
            return_value=SIMPLE_ROLE_DATA,
        ),
        patch(
            "cartography.intel.aws.iam.get_role_policy_data",
            return_value=ROLE_POLICY_DATA,
        ),
        patch(
            "cartography.intel.aws.iam.get_role_managed_policy_data", return_value={}
        ),
    ):

        # Call sync_roles to create the complete IAM structure
        common_job_parameters = {"AWS_ID": TEST_ACCOUNT_ID}
        cartography.intel.aws.iam.sync_roles(
            neo4j_session,
            MagicMock(),
            TEST_ACCOUNT_ID,
            TEST_UPDATE_TAG,
            common_job_parameters,
        )

    # Act:
    # Call get_policies_for_principal which should trigger the bug
    # This function calls parse_statement_node and should crash with AttributeError
    # if the bug exists, or work correctly if the bug is fixed
    policies = cartography.intel.aws.iam.get_policies_for_principal(
        neo4j_session, "arn:aws:iam::000000000000:role/TestReadRole"
    )
    assert policies

    # If we reach here, the bug is fixed - now test the full permission relationships flow
    cartography.intel.aws.permission_relationships.sync(
        neo4j_session,
        None,  # boto3_session not needed for this test
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {
            "permission_relationships_file": "cartography/data/permission_relationships.yaml",
        },
    )

    # Assert: Verify the relationship was created correctly
    actual_rels = check_rels(
        neo4j_session,
        "AWSRole",
        "arn",
        "S3Bucket",
        "arn",
        "CAN_READ",
    )

    expected_rels = {
        ("arn:aws:iam::000000000000:role/TestReadRole", "arn:aws:s3:::test-bucket")
    }

    assert (
        actual_rels == expected_rels
    ), f"Expected CAN_READ relationship not found. Got: {actual_rels}"
