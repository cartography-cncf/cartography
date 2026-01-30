from cartography.client.aws.iam import get_aws_admin_like_principals
from cartography.client.core.tx import load
from cartography.intel.aws.iam import _transform_policy_statements
from cartography.intel.aws.iam import load_groups
from cartography.intel.aws.iam import load_policy_statements
from cartography.intel.aws.iam import transform_groups
from cartography.models.aws.iam.inline_policy import AWSInlinePolicySchema
from tests.data.aws.iam import INLINE_POLICY_STATEMENTS
from tests.data.aws.iam import LIST_GROUPS

TEST_ACCOUNT_ID = "000000000000"
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

    # Transform the raw AWS data to the format expected by the schema
    group_data = transform_groups(LIST_GROUPS["Groups"], {})
    load_groups(
        neo4j_session,
        group_data,
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
    )
    policy_id = "arn:aws:iam::000000000000:group/example-group-0/example-group-0/inline_policy/group_inline_policy"
    inline_policy_data = [
        {
            "id": policy_id,
            "arn": None,
            "name": "group_inline_policy",
            "type": "inline",
            "principal_arns": ["arn:aws:iam::000000000000:group/example-group-0"],
        }
    ]
    load(
        neo4j_session,
        AWSInlinePolicySchema(),
        inline_policy_data,
        lastupdated=TEST_UPDATE_TAG,
        AWS_ID=TEST_ACCOUNT_ID,
    )

    # Transform the policy statements to the format expected by the schema
    transformed_statements = _transform_policy_statements(
        INLINE_POLICY_STATEMENTS, policy_id
    )
    load_policy_statements(
        neo4j_session,
        transformed_statements,
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
        "account_id": "000000000000",
        "principal_name": "example-group-0",
        "policy_name": "group_inline_policy",
    }
