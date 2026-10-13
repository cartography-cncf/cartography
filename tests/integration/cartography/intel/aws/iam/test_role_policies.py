from unittest import mock
from unittest.mock import MagicMock

import cartography.intel.aws.iam
from cartography.intel.aws.iam import sync_roles
from tests.data.aws.iam.user_policies import GET_ROLE_INLINE_POLS_SAMPLE
from tests.data.aws.iam.user_policies import GET_ROLE_LIST_DATA

AWS_UPDATE_TAG = 111111
AWS_ACCOUNT_ID = "1234"
PARAMS = {"UPDATE_TAG": AWS_UPDATE_TAG, "AWS_ID": AWS_ACCOUNT_ID}


@mock.patch.object(
    cartography.intel.aws.iam,
    "sync_role_managed_policies",
)  # because this test is for inline pols only
@mock.patch.object(
    cartography.intel.aws.iam,
    "get_role_list_data",
    return_value=GET_ROLE_LIST_DATA,
)
@mock.patch.object(
    cartography.intel.aws.iam,
    "get_role_policy_data",
    return_value=GET_ROLE_INLINE_POLS_SAMPLE,
)
def test_sync_role_inline_policies(
    mock_get_role_inline_pols: MagicMock,
    mock_get_role_list: MagicMock,
    mock_sync_role_managed_pols: MagicMock,
    neo4j_session,
) -> None:
    # Arrange
    boto3_session = mock.MagicMock()
    neo4j_session.run("MERGE (a:AWSAccount{id:$AccountId})", AccountId=AWS_ACCOUNT_ID)

    # Act
    sync_roles(neo4j_session, boto3_session, AWS_ACCOUNT_ID, AWS_UPDATE_TAG, PARAMS)

    # Assert that we create policies with expected values for ids.
    result = neo4j_session.run(
        """
        MATCH (role:AWSRole)-[:POLICY]->(pol:AWSPolicy) RETURN role.arn, pol.id;
        """,
    )

    # Define the relationships we expect in terms of role ARN and principal ARN.
    expected = {
        (
            "arn:aws:iam::1234:role/ServiceRole",
            "arn:aws:iam::1234:role/ServiceRole/inline_policy/ServiceRole",
        ),
        (
            "arn:aws:iam::1234:role/admin",
            "arn:aws:iam::1234:role/admin/inline_policy/AdministratorAccess",
        ),
    }
    actual = {(r["role.arn"], r["pol.id"]) for r in result}
    # Compare our actual results to our expected results.
    assert actual == expected
