import pytest

from cartography.intel.aws import iam
from tests.data.aws.iam import LIST_ROLES
from tests.data.aws.iam import LIST_USERS
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_UPDATE_TAG = 123456789


@pytest.mark.parametrize("revoke_trust", [False, True])
def test_assumerole_access_uses_current_trust(neo4j_session, revoke_trust):
    # Arrange: a user may assume a role only while its trust policy names that user.
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    user = LIST_USERS["Users"][0]
    role = LIST_ROLES["Roles"][0]
    user_arn, role_arn = user["Arn"], role["Arn"]
    users = iam.transform_users([user])
    policy = iam.transform_policy_data(
        {
            user_arn: {
                "assume-target": [
                    {
                        "Effect": "Allow",
                        "Action": "sts:AssumeRole",
                        "Resource": role_arn,
                    },
                ],
            },
        },
        iam.PolicyType.inline.value,
    )
    trust_statement = {
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Principal": {"AWS": user_arn},
    }
    neo4j_session.run("CREATE (:AWSAccount {id: $id})", id=TEST_ACCOUNT_ID)

    for tag, trusted in (
        (TEST_UPDATE_TAG, True),
        (TEST_UPDATE_TAG + 1, not revoke_trust),
    ):
        # Arrange: refresh identity permissions on both syncs; only trust may change.
        iam.load_users(neo4j_session, users, TEST_ACCOUNT_ID, tag)
        iam.load_policy_data(neo4j_session, policy, tag, TEST_ACCOUNT_ID)
        roles = {
            "Roles": [
                {
                    **role,
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [trust_statement] if trusted else [],
                    },
                },
            ],
        }
        parameters = {"AWS_ID": TEST_ACCOUNT_ID, "UPDATE_TAG": tag}

        # Act: derive access before IAM cleanup, in the production sync order.
        iam.sync_role_assumptions(neo4j_session, roles, TEST_ACCOUNT_ID, tag)
        iam.sync_assumerole_relationships(
            neo4j_session, TEST_ACCOUNT_ID, tag, parameters
        )
        iam.cleanup_iam(neo4j_session, parameters)

        # Assert: revocation removes derived access in the same completed sync.
        assert check_nodes(neo4j_session, "AWSUser", ["arn"]) == {(user_arn,)}
        assert check_nodes(neo4j_session, "AWSRole", ["arn"]) == {(role_arn,)}
        assert iam.get_policies_for_principal(neo4j_session, user_arn)
        assert check_rels(
            neo4j_session,
            "AWSRole",
            "arn",
            "AWSPrincipal",
            "arn",
            "TRUSTS_AWS_PRINCIPAL",
        ) == ({(role_arn, user_arn)} if trusted else set())
        assert check_rels(
            neo4j_session, "AWSUser", "arn", "AWSRole", "arn", "STS_ASSUMEROLE_ALLOW"
        ) == ({(user_arn, role_arn)} if trusted else set())
