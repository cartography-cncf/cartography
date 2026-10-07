import datetime
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from cartography.intel.aws import iam
from cartography.intel.aws.iam import PolicyType
from cartography.intel.aws.iam import transform_policy_data
from tests.data.aws.iam.mfa_devices import LIST_MFA_DEVICES
from tests.data.aws.iam.server_certificates import LIST_SERVER_CERTIFICATES_RESPONSE

SINGLE_STATEMENT = {
    "Resource": "*",
    "Action": "*",
}

# Example principal field in an AWS policy statement
# see: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
SINGLE_PRINCIPAL = {
    "AWS": "test-role-1",
    "Service": ["test-service-1", "test-service-2"],
    "Federated": "test-provider-1",
}


def test__generate_policy_statements():
    statements = iam._transform_policy_statements(SINGLE_STATEMENT, "test_policy_id")
    assert isinstance(statements, list)
    assert isinstance(statements[0]["Action"], list)
    assert isinstance(statements[0]["Resource"], list)
    assert statements[0]["id"] == "test_policy_id/statement/1"


def test__parse_principal_entries():
    principal_entries = iam._parse_principal_entries(SINGLE_PRINCIPAL)
    assert isinstance(principal_entries, list)
    assert len(principal_entries) == 4
    assert principal_entries[0] == ("AWS", "test-role-1")
    assert principal_entries[1] == ("Service", "test-service-1")
    assert principal_entries[2] == ("Service", "test-service-2")
    assert principal_entries[3] == ("Federated", "test-provider-1")


def test_get_account_from_arn():
    result = iam.get_account_from_arn("arn:aws:iam::081157660428:role/TestRole")
    assert result == "081157660428"


def test__get_role_tags_valid_tags(mocker):
    mocker.patch(
        "cartography.intel.aws.iam.get_role_list_data",
        return_value={
            "Roles": [
                {
                    "RoleName": "test-role",
                    "Arn": "test-arn",
                },
            ],
        },
    )
    mocker.patch("boto3.session.Session")
    mock_session = mocker.Mock()
    mock_client = mocker.Mock()
    mock_role = mocker.Mock()
    mock_role.tags = [
        {
            "Key": "k1",
            "Value": "v1",
        },
    ]
    mock_client.Role.return_value = mock_role
    mock_session.resource.return_value = mock_client
    result = iam.get_role_tags(mock_session)

    assert result == [
        {
            "ResourceARN": "test-arn",
            "Tags": [
                {
                    "Key": "k1",
                    "Value": "v1",
                },
            ],
        },
    ]


def test__get_role_tags_no_tags(mocker):
    mocker.patch(
        "cartography.intel.aws.iam.get_role_list_data",
        return_value={
            "Roles": [
                {
                    "RoleName": "test-role",
                    "Arn": "test-arn",
                },
            ],
        },
    )
    mocker.patch("boto3.session.Session")
    mock_session = mocker.Mock()
    mock_client = mocker.Mock()
    mock_role = mocker.Mock()
    mock_role.tags = []
    mock_client.Role.return_value = mock_role
    mock_session.resource.return_value = mock_client
    result = iam.get_role_tags(mock_session)

    assert result == []


def test__get_role_tags_no_such_entity(mocker):
    mocker.patch(
        "cartography.intel.aws.iam.get_role_list_data",
        return_value={
            "Roles": [
                {
                    "RoleName": "deleted-role",
                    "Arn": "deleted-role-arn",
                },
            ],
        },
    )
    mock_session = mocker.Mock()
    mock_client = mocker.Mock()

    class NoSuchEntityException(Exception):
        pass

    mock_client.meta.client.exceptions.NoSuchEntityException = NoSuchEntityException
    mock_client.Role.side_effect = NoSuchEntityException()
    mock_session.resource.return_value = mock_client

    result = iam.get_role_tags(mock_session)

    assert result == []


def test__get_user_tags_valid_tags(mocker):
    mocker.patch(
        "cartography.intel.aws.iam.get_user_list_data",
        return_value={
            "Users": [
                {
                    "UserName": "test-user",
                    "Arn": "test-user-arn",
                },
            ],
        },
    )
    mocker.patch("boto3.session.Session")
    mock_session = mocker.Mock()
    mock_client = mocker.Mock()
    mock_user = mocker.Mock()
    mock_user.tags = [
        {
            "Key": "k1",
            "Value": "v1",
        },
    ]
    mock_client.User.return_value = mock_user
    mock_session.resource.return_value = mock_client

    result = iam.get_user_tags(mock_session)

    assert result == [
        {
            "ResourceARN": "test-user-arn",
            "Tags": [
                {
                    "Key": "k1",
                    "Value": "v1",
                },
            ],
        },
    ]


def test__get_user_tags_no_tags(mocker):
    mocker.patch(
        "cartography.intel.aws.iam.get_user_list_data",
        return_value={
            "Users": [
                {
                    "UserName": "test-user",
                    "Arn": "test-user-arn",
                },
            ],
        },
    )
    mocker.patch("boto3.session.Session")
    mock_session = mocker.Mock()
    mock_client = mocker.Mock()
    mock_user = mocker.Mock()
    mock_user.tags = []
    mock_client.User.return_value = mock_user
    mock_session.resource.return_value = mock_client

    result = iam.get_user_tags(mock_session)

    assert result == []


def test__get_user_tags_no_such_entity(mocker):
    mocker.patch(
        "cartography.intel.aws.iam.get_user_list_data",
        return_value={
            "Users": [
                {
                    "UserName": "deleted-user",
                    "Arn": "deleted-user-arn",
                },
            ],
        },
    )
    mock_session = mocker.Mock()
    mock_client = mocker.Mock()

    class NoSuchEntityException(Exception):
        pass

    mock_client.meta.client.exceptions.NoSuchEntityException = NoSuchEntityException
    mock_client.User.side_effect = NoSuchEntityException()
    mock_session.resource.return_value = mock_client

    result = iam.get_user_tags(mock_session)

    assert result == []


def test_transform_policy_data_correctly_creates_lists_of_statements():
    # "pol-name" is a policy containing a single statement
    # See https://github.com/cartography-cncf/cartography/issues/1102
    pol_statement_map = {
        "some-arn": {
            "pol-name": {
                "Effect": "Allow",
                "Action": "secretsmanager:GetSecretValue",
                "Resource": "arn:aws:secretsmanager:XXXXX:XXXXXXXX",
            },
        },
    }

    # Act: call transform on the object
    result = transform_policy_data(pol_statement_map, PolicyType.inline.value)

    # Assert the structure of the result
    assert len(result.inline_policies) == 1
    assert len(result.managed_policies) == 0
    assert len(result.statements_by_policy_id) == 1

    # Check the inline policy data
    expected_policy_id = "some-arn/inline_policy/pol-name"
    expected_inline_policies = [
        {
            "id": expected_policy_id,
            "name": "pol-name",
            "type": "inline",
            "arn": None,  # Inline policies don't have ARNs
            "principal_arns": ["some-arn"],
        }
    ]
    assert result.inline_policies == expected_inline_policies

    # Check the statements
    assert expected_policy_id in result.statements_by_policy_id
    statements = result.statements_by_policy_id[expected_policy_id]
    assert isinstance(statements, list)
    assert len(statements) == 1

    # Check the statements
    expected_statements = [
        {
            "id": f"{expected_policy_id}/statement/1",
            "policy_id": expected_policy_id,
            "Effect": "Allow",
            "Sid": None,  # No Sid in original statement
            "Action": ["secretsmanager:GetSecretValue"],
            "Resource": ["arn:aws:secretsmanager:XXXXX:XXXXXXXX"],
        }
    ]
    assert statements == expected_statements


def test_transform_server_certificates():
    raw_data = LIST_SERVER_CERTIFICATES_RESPONSE["ServerCertificateMetadataList"]
    result = iam.transform_server_certificates(raw_data)
    assert len(result) == 1
    assert result[0]["ServerCertificateName"] == "test-cert"
    assert isinstance(result[0]["Expiration"], datetime.datetime)
    assert isinstance(result[0]["UploadDate"], datetime.datetime)
    assert result[0]["Expiration"] == datetime.datetime(2024, 1, 1, 0, 0, 0)
    assert result[0]["UploadDate"] == datetime.datetime(2023, 1, 1, 0, 0, 0)


def test_transform_mfa_devices():
    raw_data = LIST_MFA_DEVICES
    result = iam.transform_mfa_devices(raw_data)
    assert len(result) == 3

    assert result[0]["serialnumber"] == "arn:aws:iam::000000000000:mfa/user-0"
    assert result[0]["username"] == "user-0"
    assert result[0]["user_arn"] == "arn:aws:iam::000000000000:user/user-0"
    assert result[0]["enabledate"] == "2024-01-15 10:30:00"
    assert isinstance(result[0]["enabledate_dt"], datetime.datetime)
    assert result[0]["enabledate_dt"] == datetime.datetime(2024, 1, 15, 10, 30, 0)

    assert result[1]["serialnumber"] == "arn:aws:iam::000000000000:mfa/user-0-backup"
    assert result[1]["username"] == "user-0"
    assert result[1]["user_arn"] == "arn:aws:iam::000000000000:user/user-0"
    assert result[1]["enabledate"] == "2024-02-20 14:45:00"
    assert isinstance(result[1]["enabledate_dt"], datetime.datetime)
    assert result[1]["enabledate_dt"] == datetime.datetime(2024, 2, 20, 14, 45, 0)

    assert result[2]["serialnumber"] == "arn:aws:iam::000000000000:mfa/user-1"
    assert result[2]["username"] == "user-1"
    assert result[2]["user_arn"] == "arn:aws:iam::000000000000:user/user-1"
    assert result[2]["enabledate"] == "2023-12-01 09:00:00"
    assert isinstance(result[2]["enabledate_dt"], datetime.datetime)
    assert result[2]["enabledate_dt"] == datetime.datetime(2023, 12, 1, 9, 0, 0)


def test_transform_mfa_devices_empty():
    raw_data = []
    result = iam.transform_mfa_devices(raw_data)
    assert result == []


def test_get_saml_providers_access_denied_returns_empty_list():
    # @aws_handle_regions swallows AccessDenied and returns []; the getter and
    # its caller must tolerate that instead of crashing the account sync.
    session = MagicMock()
    client = session.client.return_value
    client.list_saml_providers.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}},
        "ListSAMLProviders",
    )

    result = iam.get_saml_providers(session)

    assert result == []
    # transform_policy_data feeds the same [] fallback from sibling getters.
    transformed = transform_policy_data([], PolicyType.inline.value)
    assert transformed.statements_by_policy_id == {}


def _mock_iam_resource_with_shared_policy(mocker, role_policy_arns):
    roles = {}
    for role_name, policy_arns in role_policy_arns.items():
        role = mocker.Mock()
        role.attached_policies.all.return_value = [
            mocker.Mock(arn=arn) for arn in policy_arns
        ]
        roles[role_name] = role

    resource_client = mocker.Mock()
    resource_client.meta.client.exceptions.NoSuchEntityException = type(
        "NoSuchEntityException", (Exception,), {}
    )
    resource_client.Role.side_effect = lambda name: roles[name]

    def make_policy(arn):
        policy = mocker.Mock()
        policy.default_version.document = {"Statement": [{"Sid": arn}]}
        return policy

    resource_client.Policy.side_effect = make_policy
    session = mocker.Mock()
    session.resource.return_value = resource_client
    return session, resource_client


def test_get_role_managed_policy_data_fetches_each_policy_once(mocker):
    shared_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
    own_arn = "arn:aws:iam::000000000000:policy/role-b-policy"
    session, resource_client = _mock_iam_resource_with_shared_policy(
        mocker,
        {"role-a": [shared_arn], "role-b": [shared_arn, own_arn]},
    )
    role_list = [
        {"RoleName": "role-a", "Arn": "arn:aws:iam::000000000000:role/role-a"},
        {"RoleName": "role-b", "Arn": "arn:aws:iam::000000000000:role/role-b"},
    ]

    result = iam.get_role_managed_policy_data(session, role_list)

    assert result == {
        "arn:aws:iam::000000000000:role/role-a": {
            shared_arn: [{"Sid": shared_arn}],
        },
        "arn:aws:iam::000000000000:role/role-b": {
            shared_arn: [{"Sid": shared_arn}],
            own_arn: [{"Sid": own_arn}],
        },
    }
    assert [c.args[0] for c in resource_client.Policy.call_args_list] == [
        shared_arn,
        own_arn,
    ]


def test_get_role_managed_policy_data_retry_reuses_fetched_policies(mocker):
    mocker.patch("time.sleep")
    first_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
    throttled_arn = "arn:aws:iam::000000000000:policy/role-b-policy"
    session, resource_client = _mock_iam_resource_with_shared_policy(
        mocker,
        {"role-a": [first_arn], "role-b": [throttled_arn]},
    )
    make_policy = resource_client.Policy.side_effect
    throttled_once = []

    def throttle_first_lookup_of_second_policy(arn):
        if arn == throttled_arn and not throttled_once:
            throttled_once.append(arn)
            raise ClientError(
                {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
                "GetPolicy",
            )
        return make_policy(arn)

    resource_client.Policy.side_effect = throttle_first_lookup_of_second_policy
    role_list = [
        {"RoleName": "role-a", "Arn": "arn:aws:iam::000000000000:role/role-a"},
        {"RoleName": "role-b", "Arn": "arn:aws:iam::000000000000:role/role-b"},
    ]

    result = iam.get_role_managed_policy_data(
        session, role_list, policy_statement_cache={}
    )

    assert set(result) == {
        "arn:aws:iam::000000000000:role/role-a",
        "arn:aws:iam::000000000000:role/role-b",
    }
    assert [c.args[0] for c in resource_client.Policy.call_args_list] == [
        first_arn,
        throttled_arn,
        throttled_arn,
    ]


def _gaad_policy(arn, statements, extra_versions=0):
    versions = [
        {
            "VersionId": f"v{i}",
            "IsDefaultVersion": False,
            "Document": {"Statement": [{"Sid": "old"}]},
        }
        for i in range(extra_versions)
    ]
    versions.append(
        {
            "VersionId": "vdefault",
            "IsDefaultVersion": True,
            "Document": {"Statement": statements},
        }
    )
    return {"Arn": arn, "PolicyVersionList": versions}


SHARED_POLICY_ARN = "arn:aws:iam::aws:policy/ReadOnlyAccess"
LOCAL_POLICY_ARN = "arn:aws:iam::000000000000:policy/local"
UNATTACHED_POLICY_ARN = "arn:aws:iam::000000000000:policy/unattached"
USER_ARN = "arn:aws:iam::000000000000:user/alice"
GROUP_ARN = "arn:aws:iam::000000000000:group/admins"
EMPTY_GROUP_ARN = "arn:aws:iam::000000000000:group/empty"
ROLE_ARN = "arn:aws:iam::000000000000:role/app"

GAAD_PAGE_1 = {
    "UserDetailList": [
        {
            "Arn": USER_ARN,
            "GroupList": ["admins"],
            "UserPolicyList": [
                {"PolicyName": "inline-user", "PolicyDocument": {"Statement": "u"}}
            ],
            "AttachedManagedPolicies": [{"PolicyArn": SHARED_POLICY_ARN}],
        }
    ],
    "GroupDetailList": [
        {
            "Arn": GROUP_ARN,
            "GroupName": "admins",
            "GroupPolicyList": [],
            "AttachedManagedPolicies": [{"PolicyArn": SHARED_POLICY_ARN}],
        },
        {
            "Arn": EMPTY_GROUP_ARN,
            "GroupName": "empty",
            "GroupPolicyList": [],
            "AttachedManagedPolicies": [],
        },
    ],
    "RoleDetailList": [],
    "Policies": [_gaad_policy(SHARED_POLICY_ARN, ["shared"], extra_versions=3)],
    "IsTruncated": True,
    "Marker": "page-2",
}
GAAD_PAGE_2 = {
    "UserDetailList": [],
    "GroupDetailList": [],
    "RoleDetailList": [
        {
            "Arn": ROLE_ARN,
            "RolePolicyList": [
                {"PolicyName": "inline-role", "PolicyDocument": {"Statement": "r"}}
            ],
            "AttachedManagedPolicies": [
                {"PolicyArn": SHARED_POLICY_ARN},
                {"PolicyArn": LOCAL_POLICY_ARN},
            ],
        }
    ],
    "Policies": [
        _gaad_policy(LOCAL_POLICY_ARN, ["local"]),
        _gaad_policy(UNATTACHED_POLICY_ARN, ["unattached"]),
    ],
    "IsTruncated": False,
}


def _gaad_session(mocker, pages):
    client = mocker.Mock()
    client.get_account_authorization_details.side_effect = pages
    resource_client = mocker.Mock()
    session = mocker.Mock()
    session.client.return_value = client
    session.resource.return_value = resource_client
    return session, client, resource_client


def test_get_account_authorization_details_builds_policy_maps(mocker):
    session, client, resource_client = _gaad_session(mocker, [GAAD_PAGE_1, GAAD_PAGE_2])
    cache: dict = {}

    details = iam.get_account_authorization_details(session, cache)

    assert details.user_inline_policies == {USER_ARN: {"inline-user": "u"}}
    assert details.user_managed_policies == {USER_ARN: {SHARED_POLICY_ARN: ["shared"]}}
    assert details.group_inline_policies == {GROUP_ARN: {}, EMPTY_GROUP_ARN: {}}
    assert details.group_managed_policies == {
        GROUP_ARN: {SHARED_POLICY_ARN: ["shared"]},
        EMPTY_GROUP_ARN: {},
    }
    assert details.group_memberships == {GROUP_ARN: [USER_ARN], EMPTY_GROUP_ARN: []}
    assert details.role_inline_policies == {ROLE_ARN: {"inline-role": "r"}}
    assert details.role_managed_policies == {
        ROLE_ARN: {SHARED_POLICY_ARN: ["shared"], LOCAL_POLICY_ARN: ["local"]}
    }
    # Only default versions are kept, and nothing is fetched per policy.
    assert cache[SHARED_POLICY_ARN] == ["shared"]
    resource_client.Policy.assert_not_called()
    assert [
        c.kwargs.get("Marker")
        for c in client.get_account_authorization_details.call_args_list
    ] == [None, "page-2"]


def test_get_account_authorization_details_fetches_policy_missing_from_snapshot(
    mocker,
):
    page = {**GAAD_PAGE_2, "Policies": []}
    session, _, resource_client = _gaad_session(mocker, [page])
    fetched = mocker.Mock()
    fetched.default_version.document = {"Statement": ["fetched"]}
    resource_client.Policy.return_value = fetched

    details = iam.get_account_authorization_details(session)

    assert details.role_managed_policies[ROLE_ARN][LOCAL_POLICY_ARN] == ["fetched"]


def test_get_account_authorization_details_returns_none_without_permission(mocker):
    denied = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "not authorized"}},
        "GetAccountAuthorizationDetails",
    )
    session, _, _ = _gaad_session(mocker, [denied])

    assert iam.get_account_authorization_details(session) is None


def test_get_account_authorization_details_resumes_page_after_throttle(mocker):
    mocker.patch("time.sleep")
    throttled = ClientError(
        {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
        "GetAccountAuthorizationDetails",
    )
    session, client, _ = _gaad_session(mocker, [GAAD_PAGE_1, throttled, GAAD_PAGE_2])

    details = iam.get_account_authorization_details(session)

    assert ROLE_ARN in details.role_managed_policies
    assert [
        c.kwargs.get("Marker")
        for c in client.get_account_authorization_details.call_args_list
    ] == [None, "page-2", "page-2"]
