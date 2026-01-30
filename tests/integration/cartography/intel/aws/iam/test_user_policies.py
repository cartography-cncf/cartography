from unittest import mock
from unittest.mock import MagicMock

import cartography.intel.aws.iam
from cartography.intel.aws.iam import sync_users
from tests.data.aws.iam.user_policies import GET_USER_LIST_DATA
from tests.data.aws.iam.user_policies import GET_USER_MANAGED_POLS_SAMPLE

AWS_UPDATE_TAG = 111111
AWS_ACCOUNT_ID = "000000"
PARAMS = {"UPDATE_TAG": AWS_UPDATE_TAG, "AWS_ID": AWS_ACCOUNT_ID}


@mock.patch.object(
    cartography.intel.aws.iam,
    "sync_user_inline_policies",
)  # because this test is for managed pols only
@mock.patch.object(
    cartography.intel.aws.iam,
    "get_user_list_data",
    return_value=GET_USER_LIST_DATA,
)
@mock.patch.object(
    cartography.intel.aws.iam,
    "get_user_managed_policy_data",
    return_value=GET_USER_MANAGED_POLS_SAMPLE,
)
def test_sync_user_managed_policies(
    mock_get_user_pols: MagicMock,
    mock_get_user_list: MagicMock,
    mock_sync_user_inline_pols: MagicMock,
    neo4j_session,
) -> None:
    # Arrange
    boto3_session = mock.MagicMock()
    neo4j_session.run("MERGE (a:AWSAccount{id:$AccountId})", AccountId=AWS_ACCOUNT_ID)

    # Act
    sync_users(neo4j_session, boto3_session, AWS_ACCOUNT_ID, AWS_UPDATE_TAG, PARAMS)

    # Assert that we create policies with expected values for ids.
    result = neo4j_session.run(
        """
        MATCH (user:AWSUser)-[:POLICY]->(pol:AWSPolicy) RETURN user.arn, pol.id;
        """,
    )

    # Define the relationships we expect in terms of role ARN and principal ARN.
    expected = {
        ("arn:aws:iam::1234:user/user1", "arn:aws:iam::1234:policy/user1-user-policy"),
        ("arn:aws:iam::1234:user/user1", "arn:aws:iam::aws:policy/AmazonS3FullAccess"),
        (
            "arn:aws:iam::1234:user/user1",
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
        ),
        ("arn:aws:iam::1234:user/user3", "arn:aws:iam::aws:policy/AdministratorAccess"),
    }
    actual = {(r["user.arn"], r["pol.id"]) for r in result}
    # Compare our actual results to our expected results.
    assert actual == expected
