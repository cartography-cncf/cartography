from typing import Any
from typing import Callable
from typing import Dict
from unittest import mock

from moto import mock_aws
from pytest import raises

import cartography.config
import cartography.intel.aws
import cartography.util
from cartography.intel.aws.resources import RESOURCE_FUNCTIONS
from tests.data.aws.sync_kwargs import GRAPH_JOB_PARAMETERS
from tests.data.aws.sync_kwargs import make_aws_sync_test_kwargs
from tests.data.aws.sync_kwargs import TEST_REGIONS
from tests.data.aws.sync_kwargs import TEST_UPDATE_TAG
from tests.integration.util import check_nodes

# These unit tests are a sanity check for start*() and sync*() functions.

TEST_ACCOUNTS = {
    "profile1": "000000000000",
    "profile2": "000000000001",
    "profile3": "000000000002",
}

# https://stackoverflow.com/a/56687648 - Allows us to test the RESOURCE_FUNCTIONS table.
AWS_RESOURCE_FUNCTIONS_STUB: Dict[str, Callable] = {
    sync_name: mock.MagicMock()
    for sync_name in cartography.intel.aws.resources.RESOURCE_FUNCTIONS.keys()
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
    mock_boto3_session.return_value.region_name = "us-east-1"
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
        aioboto3_session_factory=mock.ANY,
    )
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(profile_name="profile2"),
        "000000000001",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session_factory=mock.ANY,
    )
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(profile_name="profile3"),
        "000000000002",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session_factory=mock.ANY,
    )
    assert [
        account_call.kwargs["aioboto3_session_factory"].keywords
        for account_call in mock_sync_one.call_args_list
    ] == [
        {"profile_name": "profile1"},
        {"profile_name": "profile2"},
        {"profile_name": "profile3"},
    ]
    mock_aioboto3_session.assert_not_called()

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
    mock_boto3_session.return_value.region_name = "us-east-1"
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
    mock_sync_one.assert_called_once_with(
        neo4j_session,
        mock_boto3_session(profile_name="spoke1"),
        "000000000099",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session_factory=mock.ANY,
    )
    assert mock_sync_one.call_args.kwargs["aioboto3_session_factory"].keywords == {
        "profile_name": "spoke1"
    }
    mock_aioboto3_session.assert_not_called()


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
    mock_boto3_session.return_value.region_name = "us-east-1"
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
    mock_sync_one.assert_called_once_with(
        neo4j_session,
        mock_boto3_session(),
        "000000000000",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session_factory=mock.ANY,
    )
    assert mock_sync_one.call_args.kwargs["aioboto3_session_factory"].keywords == {}
    mock_aioboto3_session.assert_not_called()


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


@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts_govcloud_profile_root_principal(
    mock_cleanup,
    mock_sync_organizations_for_accounts,
    mock_sync_one,
    neo4j_session,
    monkeypatch,
    tmp_path,
):
    # A configured account whose profile is in a GovCloud region gets an aws-us-gov root
    # principal, which matches the "arn:aws-us-gov:iam::<account>:root" in trust policies.
    # Arrange
    neo4j_session.run("MATCH (n:AWSRootPrincipal) DETACH DELETE n")
    config_file = tmp_path / "config"
    config_file.write_text("[profile example-gov]\nregion = us-gov-west-1\n")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config_file))
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    # Act
    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session,
        {"example-gov": "111122223333"},
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        aws_best_effort_mode=False,
        use_explicit_profile=True,
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws-us-gov:iam::111122223333:root",),
    }


@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_aws_organizations_for_accounts",
    return_value=[],
)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts_root_principal_uses_aws_regions(
    mock_cleanup,
    mock_sync_organizations_for_accounts,
    mock_sync_one,
    neo4j_session,
    monkeypatch,
    tmp_path,
):
    # With --aws-regions set, iam.sync builds the root principal with the partition of
    # those regions. The account loop must use the same partition even when the profile's
    # region is in another one, or the account ends up with two root principals.
    # Arrange
    neo4j_session.run("MATCH (n:AWSRootPrincipal) DETACH DELETE n")
    config_file = tmp_path / "config"
    config_file.write_text("[profile example]\nregion = us-east-1\n")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(config_file))
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)

    # Act
    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session,
        {"example": "111122223333"},
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        aws_best_effort_mode=False,
        regions=["us-gov-west-1"],
        use_explicit_profile=True,
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSRootPrincipal", ["arn"]) == {
        ("arn:aws-us-gov:iam::111122223333:root",),
    }


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations")
@mock.patch.object(cartography.intel.aws, "_sync_multiple_accounts", return_value=True)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_shared_public_ssm_parameters",
    return_value=None,
)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
def test_start_aws_ingestion(
    mock_perform_analysis,
    mock_sync_shared_public_ssm_parameters,
    mock_sync_multiple,
    mock_orgs,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
    monkeypatch,
):
    # Arrange
    monkeypatch.delenv("AWS_SSM_PUBLIC_PARAMETER_PREFIX_ALLOWLIST", raising=False)
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
            "aws_ssm_public_parameter_prefix_allowlist": "",
        },
    )
    mock_sync_shared_public_ssm_parameters.assert_called_once()
    shared_call_args = mock_sync_shared_public_ssm_parameters.call_args.args
    assert shared_call_args[0] is neo4j_session
    assert shared_call_args[3] == list(RESOURCE_FUNCTIONS.keys())
    assert shared_call_args[4]["aws_ssm_public_parameter_prefix_allowlist"] == ""
    assert shared_call_args[6] == test_config.aws_best_effort_mode


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations")
@mock.patch.object(cartography.intel.aws, "_sync_multiple_accounts", return_value=True)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_shared_public_ssm_parameters",
    return_value=None,
)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
def test_start_aws_ingestion_uses_public_ssm_allowlist_from_environment(
    mock_perform_analysis,
    mock_sync_shared_public_ssm_parameters,
    mock_sync_multiple,
    mock_orgs,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
    monkeypatch,
):
    monkeypatch.setenv(
        "AWS_SSM_PUBLIC_PARAMETER_PREFIX_ALLOWLIST",
        "/aws/service/bottlerocket/",
    )
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
        aws_ssm_public_parameter_prefix_allowlist=None,
    )

    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    common_job_parameters = mock_perform_analysis.call_args.args[2]
    assert (
        common_job_parameters["aws_ssm_public_parameter_prefix_allowlist"]
        == "/aws/service/bottlerocket/"
    )


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations")
@mock.patch.object(cartography.intel.aws, "_sync_multiple_accounts", return_value=True)
@mock.patch.object(
    cartography.intel.aws,
    "_sync_shared_public_ssm_parameters",
    return_value=None,
)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
def test_start_aws_ingestion_allows_disabling_public_ssm_allowlist_with_empty_string(
    mock_perform_analysis,
    mock_sync_shared_public_ssm_parameters,
    mock_sync_multiple,
    mock_orgs,
    mock_boto3,
    mock_aioboto3,
    neo4j_session,
):
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
        update_tag=TEST_UPDATE_TAG,
        aws_sync_all_profiles=True,
        aws_ssm_public_parameter_prefix_allowlist="",
    )

    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    common_job_parameters = mock_perform_analysis.call_args.args[2]
    assert common_job_parameters["aws_ssm_public_parameter_prefix_allowlist"] == ""


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
    mock_boto3.return_value.region_name = "us-east-1"
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
    mock_boto3.return_value.region_name = "us-east-1"
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
    mock_boto3.return_value.region_name = "us-east-1"
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
@mock.patch.object(cartography.util, "run_typed_analysis_job", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_typed_analysis_job", return_value=None)
def test_sync_one_account_all_sync_functions(
    mock_analysis,
    mock_guarded_analysis,
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
                aioboto3_session_factory=None,
            )
        else:
            AWS_RESOURCE_FUNCTIONS_STUB[sync_name].assert_called_with(
                **aws_sync_test_kwargs,
            )

    # Check that the boilerplate functions get called as expected. Brittle, but a good sanity check.
    assert mock_autodiscover.call_count == 0
    assert mock_cleanup.call_count == 0
    # All dependencies are present, so both guarded analyses reach the executor.
    assert mock_guarded_analysis.call_count == 2
    # LB/NACL runs directly after its explicit dependency check.
    assert mock_analysis.call_count == 1


def test_sync_one_account_uses_owned_ecr_session_factory(
    mocker,
    neo4j_session,
):
    # Arrange
    ecr_sync = mock.MagicMock()
    initial_session = mock.MagicMock(name="initial_session")
    fresh_session = mock.MagicMock(name="fresh_session")
    session_factory = mock.MagicMock(
        side_effect=[initial_session, fresh_session],
    )
    boto3_session = mock.MagicMock()
    mocker.patch.object(cartography.intel.aws, "migrate_legacy_aws_labels")
    mocker.patch.object(cartography.intel.aws, "run_typed_analysis_job")

    # Act
    with mock.patch.dict(
        cartography.intel.aws.RESOURCE_FUNCTIONS,
        {"ecr:image_layers": ecr_sync},
        clear=True,
    ):
        cartography.intel.aws._sync_one_account(
            neo4j_session,
            boto3_session,
            "111122223333",
            TEST_UPDATE_TAG,
            GRAPH_JOB_PARAMETERS,
            regions=TEST_REGIONS,
            aws_requested_syncs=["ecr:image_layers"],
            aioboto3_session_factory=session_factory,
        )

    # Assert
    assert ecr_sync.call_args.args[1] is initial_session
    assert ecr_sync.call_args.kwargs["aioboto3_session_factory"] is session_factory
    assert session_factory() is fresh_session
    assert session_factory.call_count == 2


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
@mock.patch.object(cartography.intel.aws, "run_typed_analysis_job", return_value=None)
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
    # The selected modules do not satisfy any per-account analysis dependencies.
    assert mock_analysis.call_count == 0
