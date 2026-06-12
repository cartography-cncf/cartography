import inspect
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from unittest import mock

import neo4j
from moto import mock_aws
from pytest import raises

import cartography.config
import cartography.intel.aws
import cartography.util
from cartography.intel.aws.resources import RESOURCE_FUNCTIONS

# These unit tests are a sanity check for start*() and sync*() functions.

TEST_ACCOUNTS = {
    "profile1": "000000000000",
    "profile2": "000000000001",
    "profile3": "000000000002",
}
TEST_REGIONS = ["us-east-1", "us-west-2"]
TEST_UPDATE_TAG = 123456789
GRAPH_JOB_PARAMETERS = {"UPDATE_TAG": TEST_UPDATE_TAG}

# https://stackoverflow.com/a/56687648 - Allows us to test the RESOURCE_FUNCTIONS table.
AWS_RESOURCE_FUNCTIONS_STUB: Dict[str, Callable] = {
    sync_name: mock.MagicMock()
    for sync_name in cartography.intel.aws.resources.RESOURCE_FUNCTIONS.keys()
}


def make_aws_sync_test_kwargs(
    neo4j_session: neo4j.Session,
    mock_boto3_session: mock.MagicMock,
) -> Dict[str, Any]:
    """
    Returns a dummy dict of kwargs to use for AWS sync functions.
    The keys of this dict are also used to ensure that parameter names for all sync functions are standardized; see
    `test_standardize_aws_sync_kwargs`.
    Note: aioboto3_session is NOT included here because it's only used by ecr:image_layers, which has a different
    signature from the standard AWS sync functions.
    """
    return {
        "neo4j_session": neo4j_session,
        "boto3_session": mock_boto3_session(),
        "current_aws_account_id": "1234",
        "update_tag": TEST_UPDATE_TAG,
        "regions": TEST_REGIONS,
        "common_job_parameters": GRAPH_JOB_PARAMETERS,
    }


@mock.patch.object(cartography.intel.aws.organizations, "sync", return_value=None)
@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts(
    mock_cleanup,
    mock_sync_organizations_for_accounts,
    mock_sync_one,
    mock_boto3_session,
    mock_aioboto3_session,
    mock_sync_orgs,
    neo4j_session,
):
    call_order = []
    mock_sync_organizations_for_accounts.side_effect = (
        lambda *args, **kwargs: call_order.append("organizations") or []
    )
    mock_sync_one.side_effect = lambda *args, **kwargs: call_order.append("account")

    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        aws_best_effort_mode=False,
        use_explicit_profile=True,
    )

    assert call_order == ["organizations", "account", "account", "account"]

    # Ensure we call _sync_one_account on all accounts in our list.
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(profile_name="profile1"),
        "000000000000",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(profile_name="profile1"),
    )
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(profile_name="profile2"),
        "000000000001",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(profile_name="profile2"),
    )
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(profile_name="profile3"),
        "000000000002",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(profile_name="profile3"),
    )

    # Ensure _sync_one_account is called once for each account and Organizations
    # discovery happens once before the per-account resource loop.
    assert mock_sync_one.call_count == len(TEST_ACCOUNTS.keys())
    mock_sync_organizations_for_accounts.assert_called_once_with(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        organization_account_ids=None,
        use_explicit_profile=True,
    )

    # This is a brittle test, but it is here to ensure that the mock_cleanup path is correct.
    assert mock_cleanup.call_count == 1


@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_aws_organization_for_account")
@mock.patch.object(cartography.intel.aws, "_discover_aws_organization_candidates")
def test_sync_aws_organizations_for_accounts_uses_management_candidate_first(
    mock_discover_candidates,
    mock_sync_aws_organization_for_account,
    mock_boto3_session,
    neo4j_session,
):
    # Arrange
    mock_discover_candidates.return_value = [
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "profile2",
            "000000000001",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "profile1",
            "000000000000",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
    ]
    mock_sync_aws_organization_for_account.return_value = (
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000000",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.SYNCED,
            organization_id="o-example",
        )
    )

    # Act
    cartography.intel.aws._sync_aws_organizations_for_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        use_explicit_profile=True,
    )

    # Assert
    assert [
        call.args[2] for call in mock_sync_aws_organization_for_account.call_args_list
    ] == ["000000000000"]


@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_aws_organization_for_account")
@mock.patch.object(cartography.intel.aws, "_discover_aws_organization_candidates")
def test_sync_aws_organizations_for_accounts_tries_next_candidate_after_denial(
    mock_discover_candidates,
    mock_sync_aws_organization_for_account,
    mock_boto3_session,
    neo4j_session,
):
    # Arrange
    mock_discover_candidates.return_value = [
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "profile2",
            "000000000001",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "profile1",
            "000000000000",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
    ]
    mock_sync_aws_organization_for_account.side_effect = [
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000000",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.ACCESS_DENIED,
            organization_id="o-example",
            error_code="AccessDeniedException",
        ),
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000001",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.SYNCED,
            organization_id="o-example",
        ),
    ]

    # Act
    results = cartography.intel.aws._sync_aws_organizations_for_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        use_explicit_profile=True,
    )

    # Assert
    assert [
        call.args[2] for call in mock_sync_aws_organization_for_account.call_args_list
    ] == [
        "000000000000",
        "000000000001",
    ]
    assert [result.status for result in results] == [
        cartography.intel.aws.organizations.AWSOrganizationSyncStatus.ACCESS_DENIED,
        cartography.intel.aws.organizations.AWSOrganizationSyncStatus.SYNCED,
    ]


@mock.patch.object(cartography.intel.aws, "_sync_aws_organization_for_account")
@mock.patch.object(cartography.intel.aws, "_discover_aws_organization_candidates")
def test_sync_aws_organizations_for_accounts_uses_one_default_session(
    mock_discover_candidates,
    mock_sync_aws_organization_for_account,
    neo4j_session,
):
    # Arrange
    mock_discover_candidates.return_value = [
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "default",
            "000000000000",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
    ]
    mock_sync_aws_organization_for_account.return_value = (
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000000",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.SYNCED,
            organization_id="o-example",
        )
    )

    # Act
    cartography.intel.aws._sync_aws_organizations_for_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        use_explicit_profile=False,
    )

    # Assert
    mock_discover_candidates.assert_called_once_with(TEST_ACCOUNTS, False)
    mock_sync_aws_organization_for_account.assert_called_once()


@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_aws_organization_for_account")
@mock.patch.object(cartography.intel.aws, "_discover_aws_organization_candidates")
def test_sync_aws_organizations_for_accounts_discovers_only_explicit_candidates(
    mock_discover_candidates,
    mock_sync_aws_organization_for_account,
    mock_boto3_session,
    neo4j_session,
):
    # Arrange
    mock_discover_candidates.return_value = [
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "profile2",
            "000000000001",
            organization_id="o-example",
            management_account_id="000000000001",
        ),
    ]
    mock_sync_aws_organization_for_account.return_value = (
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000001",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.SYNCED,
            organization_id="o-example",
        )
    )

    # Act
    cartography.intel.aws._sync_aws_organizations_for_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        organization_account_ids=["000000000001"],
        use_explicit_profile=True,
    )

    # Assert
    mock_discover_candidates.assert_called_once_with({"profile2": "000000000001"}, True)
    mock_boto3_session.assert_called_once_with(profile_name="profile2")
    mock_sync_aws_organization_for_account.assert_called_once()
    assert mock_sync_aws_organization_for_account.call_args.args[2] == "000000000001"


@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_aws_organization_for_account")
@mock.patch.object(cartography.intel.aws, "_discover_aws_organization_candidates")
def test_sync_aws_organizations_for_accounts_explicit_candidates_prefer_management(
    mock_discover_candidates,
    mock_sync_aws_organization_for_account,
    mock_boto3_session,
    neo4j_session,
):
    # Arrange
    mock_discover_candidates.return_value = [
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "member-profile",
            "000000000001",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "management-profile",
            "000000000000",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
    ]
    mock_sync_aws_organization_for_account.return_value = (
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000000",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.SYNCED,
            organization_id="o-example",
        )
    )

    # Act
    cartography.intel.aws._sync_aws_organizations_for_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        organization_account_ids=["000000000001", "000000000000"],
        use_explicit_profile=True,
    )

    # Assert
    mock_discover_candidates.assert_called_once_with(
        {
            "profile1": "000000000000",
            "profile2": "000000000001",
        },
        True,
    )
    assert [
        call.args[2] for call in mock_sync_aws_organization_for_account.call_args_list
    ] == ["000000000000"]


@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_aws_organization_for_account")
@mock.patch.object(cartography.intel.aws, "_discover_aws_organization_candidates")
def test_sync_aws_organizations_for_accounts_preserves_graph_when_all_candidates_fail(
    mock_discover_candidates,
    mock_sync_aws_organization_for_account,
    mock_boto3_session,
    neo4j_session,
    caplog,
):
    # Arrange
    mock_discover_candidates.return_value = [
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "member-profile",
            "000000000001",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
        cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            "management-profile",
            "000000000000",
            organization_id="o-example",
            management_account_id="000000000000",
        ),
    ]
    mock_sync_aws_organization_for_account.side_effect = [
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000000",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.ACCESS_DENIED,
            organization_id="o-example",
            error_code="AccessDeniedException",
        ),
        cartography.intel.aws.organizations.AWSOrganizationSyncResult(
            "000000000001",
            cartography.intel.aws.organizations.AWSOrganizationSyncStatus.ACCESS_DENIED,
            organization_id="o-example",
            error_code="AccessDeniedException",
        ),
    ]

    # Act
    results = cartography.intel.aws._sync_aws_organizations_for_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        use_explicit_profile=True,
    )

    # Assert
    assert [
        call.args[2] for call in mock_sync_aws_organization_for_account.call_args_list
    ] == ["000000000000", "000000000001"]
    assert [result.status for result in results] == [
        cartography.intel.aws.organizations.AWSOrganizationSyncStatus.ACCESS_DENIED,
        cartography.intel.aws.organizations.AWSOrganizationSyncStatus.ACCESS_DENIED,
    ]
    assert (
        "Unable to find an account with access to enumerate AWS Organization o-example."
        in caplog.text
    )


def test_discover_aws_organization_candidates_keeps_account_order(mocker):
    # Arrange
    def fake_discover(profile_name, account_id, use_explicit_profile):
        return cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            profile_name,
            account_id,
            organization_id=f"org-{account_id}",
        )

    mocker.patch.object(
        cartography.intel.aws,
        "_discover_aws_organization_candidate",
        side_effect=fake_discover,
    )

    # Act
    candidates = cartography.intel.aws._discover_aws_organization_candidates(
        TEST_ACCOUNTS,
        use_explicit_profile=True,
    )

    # Assert
    assert [(c.profile_name, c.account_id) for c in candidates] == list(
        TEST_ACCOUNTS.items(),
    )


def test_discover_aws_organization_candidates_warns_when_default_session_truncates(
    mocker,
    caplog,
):
    # Arrange
    def fake_discover(profile_name, account_id, use_explicit_profile):
        return cartography.intel.aws.AWSOrganizationDiscoveryCandidate(
            profile_name,
            account_id,
            organization_id=f"org-{account_id}",
        )

    mocker.patch.object(
        cartography.intel.aws,
        "_discover_aws_organization_candidate",
        side_effect=fake_discover,
    )

    # Act
    candidates = cartography.intel.aws._discover_aws_organization_candidates(
        TEST_ACCOUNTS,
        use_explicit_profile=False,
    )

    # Assert
    assert [(c.profile_name, c.account_id) for c in candidates] == [
        ("profile1", "000000000000"),
    ]
    assert (
        "AWS Organizations discovery is using the default AWS session, so only the first configured AWS account"
        in caplog.text
    )


@mock.patch.object(cartography.intel.aws.organizations, "sync", return_value=None)
@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts_single_profile_uses_profile_name(
    mock_cleanup,
    mock_sync_organizations_for_accounts,
    mock_sync_one,
    mock_boto3_session,
    mock_aioboto3_session,
    mock_sync_orgs,
    neo4j_session,
):
    # Regression for #1142 and #1185: single explicit profile must not fall back to the default session.
    single_account = {"spoke1": "000000000099"}

    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session,
        single_account,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        aws_best_effort_mode=False,
        use_explicit_profile=True,
    )

    mock_boto3_session.assert_any_call(profile_name="spoke1")
    mock_aioboto3_session.assert_any_call(profile_name="spoke1")
    mock_sync_one.assert_called_once_with(
        neo4j_session,
        mock_boto3_session(profile_name="spoke1"),
        "000000000099",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(profile_name="spoke1"),
    )


@mock.patch.object(cartography.intel.aws.organizations, "sync", return_value=None)
@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts_default_path_uses_default_session(
    mock_cleanup,
    mock_sync_organizations_for_accounts,
    mock_sync_one,
    mock_boto3_session,
    mock_aioboto3_session,
    mock_sync_orgs,
    neo4j_session,
):
    # Without --aws-sync-all-profiles the default session must be used (preserves #1042 fix for env-var-only creds).
    default_account = {"default": "000000000000"}

    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session,
        default_account,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        aws_best_effort_mode=False,
        use_explicit_profile=False,
    )

    for call in mock_boto3_session.call_args_list:
        assert "profile_name" not in call.kwargs
    for call in mock_aioboto3_session.call_args_list:
        assert "profile_name" not in call.kwargs
    assert mock_sync_one.call_count == 1


@mock_aws
@mock.patch.object(cartography.intel.aws.organizations, "sync", return_value=None)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts_profile_session_is_usable(
    mock_cleanup,
    mock_sync_organizations_for_accounts,
    mock_sync_orgs,
    neo4j_session,
    monkeypatch,
    tmp_path,
):
    # Smoke test for #1042/#1142/#1185: the real boto3 Session built for each profile
    # must resolve credentials from the configured profile and support live AWS calls.
    # Unlike the mocked plumbing tests above, nothing patches boto3.Session here.
    creds_file = tmp_path / "credentials"
    creds_file.write_text(
        "[spoke1]\n"
        "aws_access_key_id = spoke-access\n"
        "aws_secret_access_key = spoke-secret\n",
    )
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(creds_file))
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    captured_sessions = []

    def capture(neo4j_session, boto3_session, *args, **kwargs):
        captured_sessions.append(boto3_session)

    with mock.patch.object(
        cartography.intel.aws, "_sync_one_account", side_effect=capture
    ):
        cartography.intel.aws._sync_multiple_accounts(
            neo4j_session,
            {"spoke1": "000000000099"},
            TEST_UPDATE_TAG,
            GRAPH_JOB_PARAMETERS,
            aws_best_effort_mode=False,
            use_explicit_profile=True,
        )

    assert len(captured_sessions) == 1
    session = captured_sessions[0]
    assert session.profile_name == "spoke1"
    creds = session.get_credentials()
    assert creds is not None
    assert creds.access_key == "spoke-access"
    # The session is good enough to call STS through moto — if profile_name weren't
    # honored, this would fail with NoCredentialsError (empty creds file).
    identity = session.client("sts", region_name="us-east-1").get_caller_identity()
    assert "Account" in identity


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations")
@mock.patch.object(cartography.intel.aws, "_sync_multiple_accounts", return_value=True)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
def test_start_aws_ingestion(
    mock_perform_analysis,
    mock_sync_multiple,
    mock_orgs,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
):
    # Arrange
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
        experimental_aws_inspector_batch=100,
        aws_tagging_api_cleanup_batch=1000,
    )

    # Act
    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    # Assert
    assert mock_sync_multiple.call_count == 1
    assert mock_sync_multiple.call_args.kwargs["organization_account_ids"] is None
    mock_perform_analysis.assert_called_once_with(
        list(RESOURCE_FUNCTIONS.keys()),
        neo4j_session,
        {
            "UPDATE_TAG": test_config.update_tag,
            "permission_relationships_file": test_config.permission_relationships_file,
            "aws_guardduty_severity_threshold": None,
            "aws_cloudtrail_management_events_lookback_hours": test_config.aws_cloudtrail_management_events_lookback_hours,
            "experimental_aws_inspector_batch": test_config.experimental_aws_inspector_batch,
            "aws_tagging_api_cleanup_batch": test_config.aws_tagging_api_cleanup_batch,
        },
    )


def test_kms_syncs_before_kms_dependent_resources():
    """Resources that wire ENCRYPTED_BY edges by matching existing KMSKey nodes
    (s3, rds, efs, dynamodb) must sync after kms, otherwise the edges are silently
    missed on a full sync."""
    order = list(RESOURCE_FUNCTIONS.keys())
    kms_index = order.index("kms")
    for dependent in ("s3", "rds", "efs", "dynamodb"):
        assert kms_index < order.index(dependent), (
            f"'kms' must sync before '{dependent}' so the ENCRYPTED_BY edge can "
            f"match existing KMSKey nodes"
        )


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations")
@mock.patch.object(cartography.intel.aws, "_sync_multiple_accounts", return_value=True)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
def test_start_aws_ingestion_passes_organization_account_ids(
    mock_perform_analysis,
    mock_sync_multiple,
    mock_orgs,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
):
    # Arrange
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
        aws_organization_account_ids="000000000000, 000000000001",
    )

    # Act
    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    # Assert
    assert mock_sync_multiple.call_args.kwargs["organization_account_ids"] == [
        "000000000000",
        "000000000001",
    ]


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations.get_aws_accounts_from_botocore_config")
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job")
def test_start_aws_ingestion_raises_aggregated_exceptions_with_aws_best_effort_mode(
    mock_run_cleanup_job,
    mock_perform_analysis,
    mock_sync_one,
    mock_sync_organizations_for_accounts,
    mock_get_aws_account,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
):
    # Arrange
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
        aws_best_effort_mode=True,
    )
    mock_sync_one.side_effect = KeyError("foo")
    mock_get_aws_account.return_value = {
        "test_profile": "test_account",
        "test_profile2": "test_account2",
    }

    # Act
    with raises(Exception) as e:
        cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    # Assert
    message = str(e.value)
    assert message.count("KeyError") == 2
    assert "test_account" in message
    assert "test_account2" in message
    assert mock_sync_one.call_count == 2
    assert mock_sync_organizations_for_accounts.call_count == 1
    assert mock_run_cleanup_job.call_count == 0
    assert mock_perform_analysis.call_count == 0


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations.get_aws_accounts_from_botocore_config")
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job")
def test_start_aws_ingestion_raises_one_exception_without_aws_best_effort_mode(
    mock_run_cleanup_job,
    mock_perform_analysis,
    mock_sync_one,
    mock_sync_organizations_for_accounts,
    mock_get_aws_account,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
):
    # Arrange
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
    )
    mock_sync_one.side_effect = KeyError("foo")
    mock_get_aws_account.return_value = {
        "test_profile": "test_account",
        "test_profile2": "test_account2",
    }

    # Act
    with raises(Exception) as e:
        cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    # Assert
    assert "KeyError" in str(e)
    assert str(e.value).count("foo") == 1
    assert mock_sync_one.call_count == 1
    assert mock_sync_organizations_for_accounts.call_count == 1
    assert mock_run_cleanup_job.call_count == 0
    assert mock_perform_analysis.call_count == 0


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations.get_aws_accounts_from_botocore_config")
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job")
def test_start_aws_ingestion_does_cleanup(
    mock_run_cleanup_job,
    mock_perform_analysis,
    mock_sync_one,
    mock_sync_organizations_for_accounts,
    mock_get_aws_account,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
):
    # Arrange
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
    )
    mock_get_aws_account.return_value = {
        "test_profile": "test_account",
        "test_profile2": "test_account2",
    }

    # Act
    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    # Assert
    assert mock_perform_analysis.call_count == 1
    assert mock_run_cleanup_job.call_count == 1
    assert mock_sync_organizations_for_accounts.call_count == 1


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.dict(
    "cartography.intel.aws.RESOURCE_FUNCTIONS", AWS_RESOURCE_FUNCTIONS_STUB
)
@mock.patch.object(
    cartography.intel.aws.resourcegroupstaggingapi, "sync", return_value=None
)
@mock.patch("cartography.intel.aws.permission_relationships.sync")
@mock.patch.object(
    cartography.intel.aws, "_autodiscover_account_regions", return_value=TEST_REGIONS
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_scoped_analysis_job", return_value=None)
def test_sync_one_account_all_sync_functions(
    mock_analysis,
    mock_cleanup,
    mock_autodiscover,
    mock_perm_rels,
    mock_tags,
    mock_boto3_session,
    mock_aioboto3_session,
    neo4j_session,
):
    aws_sync_test_kwargs: Dict[str, Any] = make_aws_sync_test_kwargs(
        neo4j_session,
        mock_boto3_session,
    )
    cartography.intel.aws._sync_one_account(
        **aws_sync_test_kwargs,
        aioboto3_session=mock_aioboto3_session(),
    )

    # Test that ALL syncs got called.
    for sync_name in cartography.intel.aws.resources.RESOURCE_FUNCTIONS.keys():
        # ecr:image_layers has a different signature (uses aioboto3_session instead of boto3_session)
        # and is called with positional args in _sync_one_account
        if sync_name == "ecr:image_layers":
            AWS_RESOURCE_FUNCTIONS_STUB[sync_name].assert_called_with(
                neo4j_session,
                mock_aioboto3_session(),
                TEST_REGIONS,
                "1234",
                TEST_UPDATE_TAG,
                GRAPH_JOB_PARAMETERS,
            )
        else:
            AWS_RESOURCE_FUNCTIONS_STUB[sync_name].assert_called_with(
                **aws_sync_test_kwargs,
            )

    # Check that the boilerplate functions get called as expected. Brittle, but a good sanity check.
    assert mock_autodiscover.call_count == 0
    assert mock_cleanup.call_count == 0
    assert mock_analysis.call_count == 3


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch.dict(
    "cartography.intel.aws.RESOURCE_FUNCTIONS", AWS_RESOURCE_FUNCTIONS_STUB
)
@mock.patch.object(
    cartography.intel.aws.resourcegroupstaggingapi, "sync", return_value=None
)
@mock.patch("cartography.intel.aws.permission_relationships.sync")
@mock.patch.object(
    cartography.intel.aws, "_autodiscover_account_regions", return_value=TEST_REGIONS
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_scoped_analysis_job", return_value=None)
def test_sync_one_account_just_iam_rels_and_tags(
    mock_analysis,
    mock_cleanup,
    mock_autodiscover,
    mock_perm_rels,
    mock_tags,
    mock_boto3_session,
    mock_aioboto3_session,
    neo4j_session,
):
    aws_sync_test_kwargs: Dict[str, any] = make_aws_sync_test_kwargs(
        neo4j_session,
        mock_boto3_session,
    )
    cartography.intel.aws._sync_one_account(
        neo4j_session,
        mock_boto3_session(),
        "1234",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        aws_requested_syncs=[
            "iam",
            "permission_relationships",
            "resourcegroupstaggingapi",
        ],
    )

    # Test that the syncs we requested (IAM, perm rels, tags) actually got called.
    AWS_RESOURCE_FUNCTIONS_STUB["iam"].assert_called_with(**aws_sync_test_kwargs)
    AWS_RESOURCE_FUNCTIONS_STUB["permission_relationships"].assert_called_with(
        **aws_sync_test_kwargs,
    )
    AWS_RESOURCE_FUNCTIONS_STUB["resourcegroupstaggingapi"].assert_called_with(
        **aws_sync_test_kwargs,
    )

    # _sync_one_account() above did not specify regions, so we expect 1 call to _autodiscover_account_regions().
    assert mock_autodiscover.call_count == 1
    assert mock_cleanup.call_count == 0
    assert mock_analysis.call_count == 1


def test_standardize_aws_sync_kwargs():
    """
    Makes sure that we always use a standard set of parameter names for AWS syncs referenced in the
    cartography.intel.aws.resources.RESOURCE_FUNCTIONS function table. This standardization gives us
    flexibility when calling these syncs as function pointers.

    Fine print: this test excludes parameters with default values (e.g. `tag_resource_type_mappings` in
    resourcegroupstaggingapi).

    The set of standardized sync param names is maintained in
    tests.integration.cartography.intel.aws.test_init.make_aws_sync_test_kwargs.

    Exception: ecr:image_layers has a different signature (uses aioboto3_session instead of boto3_session) and is
    called with positional args in _sync_one_account, so it's excluded from this validation.
    """
    aws_sync_test_kwargs = make_aws_sync_test_kwargs(mock.MagicMock, mock.MagicMock)
    # aioboto3_session is used only by ecr:image_layers
    ecr_image_layers_kwargs = [
        "neo4j_session",
        "aioboto3_session",
        "regions",
        "current_aws_account_id",
        "update_tag",
        "common_job_parameters",
    ]

    for (
        func_name,
        sync_func,
    ) in cartography.intel.aws.resources.RESOURCE_FUNCTIONS.items():
        # ecr:image_layers has a different signature, so skip standardization check
        if func_name == "ecr:image_layers":
            all_args: List[str] = inspect.getfullargspec(sync_func).args
            if len(all_args) == 0:
                all_args = inspect.getfullargspec(sync_func.__wrapped__).args
            for arg_name in all_args:
                if (
                    inspect.signature(sync_func).parameters[arg_name].default
                    == inspect._empty
                ):
                    assert arg_name in ecr_image_layers_kwargs, (
                        f'Argument name "{arg_name}" in ecr:image_layers sync function is non-standard. '
                        f"Expected arguments: {', '.join(ecr_image_layers_kwargs)}"
                    )
            continue

        all_args: List[str] = inspect.getfullargspec(sync_func).args

        # Inspect the sync func if it is wrapped, e.g. by @timeit
        if len(all_args) == 0:
            all_args = inspect.getfullargspec(sync_func.__wrapped__).args

        for arg_name in all_args:
            valid_param_names: str = ", ".join(aws_sync_test_kwargs.keys())

            # Only enforce param names that don't have default values set.
            if (
                inspect.signature(sync_func).parameters[arg_name].default
                == inspect._empty
            ):
                assert arg_name in aws_sync_test_kwargs.keys(), (
                    f'Argument name "{arg_name}" in sync function "{sync_func.__module__}.{sync_func.__name__}" is '
                    f"non-standard. Valid ones include: {valid_param_names}. Please change your argument name to one "
                    f"of these standard ones, or if you are introducing a new argument name, then please update "
                    f"tests.integration.cartography.intel.aws.test_init.make_aws_sync_test_kwargs."
                )
