from unittest import mock
from unittest.mock import call
from unittest.mock import MagicMock

import cartography.intel.aws.iam
from cartography.intel.aws.iam import PolicyType
from cartography.intel.aws.iam import sync_user_managed_policies
from tests.data.aws.iam.user_policies import GET_USER_LIST_DATA
from tests.data.aws.iam.user_policies import GET_USER_MANAGED_POLS_SAMPLE

AWS_UPDATE_TAG = 111111


@mock.patch.object(cartography.intel.aws.iam, "load_policy")
@mock.patch.object(
    cartography.intel.aws.iam,
    "get_user_managed_policy_data",
    return_value=GET_USER_MANAGED_POLS_SAMPLE,
)
def test_sync_user_managed_policies(
    mock_get_user_pols: MagicMock,
    mock_load_pol: MagicMock,
):
    # Arrange
    boto3_session = mock.MagicMock()
    neo4j_session = mock.MagicMock()

    # Act
    sync_user_managed_policies(
        boto3_session,
        GET_USER_LIST_DATA,
        neo4j_session,
        AWS_UPDATE_TAG,
    )

    # Assert that we attempt to create policies with expected values for ids.
    mock_load_pol.assert_has_calls(
        [
            call(
                neo4j_session,
                "arn:aws:iam::1234:policy/user1-user-policy",
                "user1-user-policy",
                PolicyType.managed.value,
                "arn:aws:iam::1234:user/user1",
                AWS_UPDATE_TAG,
            ),
            call(
                neo4j_session,
                "arn:aws:iam::aws:policy/AmazonS3FullAccess",
                "AmazonS3FullAccess",
                PolicyType.managed.value,
                "arn:aws:iam::1234:user/user1",
                AWS_UPDATE_TAG,
            ),
            call(
                neo4j_session,
                "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
                "AWSLambda_FullAccess",
                PolicyType.managed.value,
                "arn:aws:iam::1234:user/user1",
                AWS_UPDATE_TAG,
            ),
            call(
                neo4j_session,
                "arn:aws:iam::aws:policy/AdministratorAccess",
                "AdministratorAccess",
                PolicyType.managed.value,
                "arn:aws:iam::1234:user/user3",
                AWS_UPDATE_TAG,
            ),
        ],
        any_order=False,
    )
