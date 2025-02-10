from cartography.client.aws.iam import get_aws_admin_like_principals
from cartography.intel.aws.iam import load_groups
from cartography.intel.aws.iam import load_policy
from cartography.intel.aws.iam import load_policy_statements
from tests.data.aws.iam import INLINE_POLICY_STATEMENTS
from tests.data.aws.iam import LIST_GROUPS

TEST_ACCOUNT_ID = "1111"
TEST_UPDATE_TAG = 0000
TEST_ACCOUNT_NAME = "testaccount"


def _ensure_test_data(neo4j_session):
    """
    Ideally we try to use actual cartography functions to populate a graph to test the client functions.
    This helps ensure that the queries in the client functions won't get stale or stop working.
    """
    neo4j_session.run(
        "MERGE (a:AWSAccount{id:$AccountId, name:$AccountName})",
        AccountId=TEST_ACCOUNT_ID,
        AccountName=TEST_ACCOUNT_NAME,
    )

    load_groups(
        neo4j_session,
        LIST_GROUPS["Groups"],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )

    load_policy(
        neo4j_session,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
        "group_inline_policy",
        "inline",
        "arn:aws:iam::000000000000:group/example-group-0",
        TEST_UPDATE_TAG,
    )

    load_policy_statements(
        neo4j_session,
        "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy",
        "group_inline_policy",
        INLINE_POLICY_STATEMENTS,
        TEST_UPDATE_TAG,
    )


def test_get_aws_admin_like_principals(neo4j_session):
    # Arrange
    _ensure_test_data(neo4j_session)

    # Act
    admin_data = get_aws_admin_like_principals(neo4j_session)

    # Assert
    assert len(admin_data) == 1
    assert admin_data[0] == {
        "account_name": "testaccount",
        "account_id": "1111",
        "principal_name": "example-group-0",
        "policy_name": "group_inline_policy",
    }
