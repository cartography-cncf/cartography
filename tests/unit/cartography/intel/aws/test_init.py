import inspect
from typing import List
from unittest import mock

import botocore.exceptions
import pytest
from pytest import mark
from pytest import raises

import cartography.intel.aws
from cartography.intel.aws.resources import RESOURCE_FUNCTIONS
from tests.data.aws.sync_kwargs import GRAPH_JOB_PARAMETERS
from tests.data.aws.sync_kwargs import make_aws_sync_test_kwargs
from tests.data.aws.sync_kwargs import TEST_UPDATE_TAG

# Sanity checks for AWS sync orchestration and the RESOURCE_FUNCTIONS table. None of them read or write the graph.

TEST_ACCOUNTS = {
    "profile1": "000000000000",
    "profile2": "000000000001",
    "profile3": "000000000002",
}
PUBLIC_SSM_JOB_PARAMETERS = {
    **GRAPH_JOB_PARAMETERS,
    "aws_ssm_public_parameter_prefix_allowlist": "/aws/service/bottlerocket/",
}


@pytest.fixture
def neo4j_session():
    # The code under test only forwards the session to mocked functions.
    return mock.MagicMock()


@mock.patch.object(cartography.intel.aws.ssm_intel, "sync_public_parameters")
@mock.patch.object(cartography.intel.aws, "_autodiscover_account_regions")
@mock.patch.object(cartography.intel.aws, "_get_boto3_session_for_profile")
def test_sync_shared_public_ssm_parameters_unions_profile_regions(
    mock_get_session,
    mock_autodiscover_regions,
    mock_sync_public_parameters,
    neo4j_session,
):
    # Arrange
    first_session = mock.MagicMock(name="first_session")
    second_session = mock.MagicMock(name="second_session")
    mock_get_session.side_effect = [first_session, second_session]
    mock_autodiscover_regions.side_effect = [
        ["us-east-1", "us-west-2"],
        ["us-west-2", "eu-west-1"],
    ]
    common_job_parameters = PUBLIC_SSM_JOB_PARAMETERS.copy()

    # Act
    cartography.intel.aws._sync_shared_public_ssm_parameters(
        neo4j_session,
        mock.MagicMock(),
        {"first": "111111111111", "second": "222222222222"},
        ["ssm"],
        common_job_parameters,
        configured_regions=None,
        aws_best_effort_mode=False,
    )

    # Assert
    region_session_candidates = mock_sync_public_parameters.call_args.args[1]
    assert list(region_session_candidates) == [
        "us-east-1",
        "us-west-2",
        "eu-west-1",
    ]
    assert region_session_candidates["us-east-1"] == [first_session]
    assert region_session_candidates["us-west-2"] == [
        first_session,
        second_session,
    ]
    assert region_session_candidates["eu-west-1"] == [second_session]
    assert mock_sync_public_parameters.call_args.kwargs["cleanup_allowed"] is True


@mock.patch.object(cartography.intel.aws.ssm_intel, "sync_public_parameters")
@mock.patch.object(cartography.intel.aws, "_autodiscover_account_regions")
@mock.patch.object(cartography.intel.aws, "_get_boto3_session_for_profile")
def test_sync_shared_public_ssm_parameters_best_effort_skips_profile_setup_failure(
    mock_get_session,
    mock_autodiscover_regions,
    mock_sync_public_parameters,
    neo4j_session,
):
    # Arrange
    working_session = mock.MagicMock(name="working_session")
    mock_get_session.side_effect = [
        botocore.exceptions.ProfileNotFound(profile="broken"),
        working_session,
    ]
    mock_autodiscover_regions.return_value = ["us-west-2"]

    # Act
    cartography.intel.aws._sync_shared_public_ssm_parameters(
        neo4j_session,
        mock.MagicMock(),
        {"broken": "111111111111", "working": "222222222222"},
        ["ssm"],
        PUBLIC_SSM_JOB_PARAMETERS.copy(),
        configured_regions=None,
        aws_best_effort_mode=True,
    )

    # Assert
    assert mock_sync_public_parameters.call_args.args[1] == {
        "us-west-2": [working_session]
    }
    assert mock_sync_public_parameters.call_args.kwargs["cleanup_allowed"] is False


@mock.patch.object(cartography.intel.aws, "_get_boto3_session_for_profile")
def test_sync_shared_public_ssm_parameters_fails_loudly_on_profile_setup_error(
    mock_get_session,
    neo4j_session,
):
    # Arrange
    mock_get_session.side_effect = botocore.exceptions.ProfileNotFound(profile="broken")

    # Act and assert
    with raises(botocore.exceptions.ProfileNotFound):
        cartography.intel.aws._sync_shared_public_ssm_parameters(
            neo4j_session,
            mock.MagicMock(),
            {"broken": "111111111111"},
            ["ssm"],
            PUBLIC_SSM_JOB_PARAMETERS.copy(),
            configured_regions=None,
            aws_best_effort_mode=False,
        )


@mock.patch.object(
    cartography.intel.aws.ssm_intel,
    "sync_public_parameters",
    side_effect=RuntimeError("load failed"),
)
def test_sync_shared_public_ssm_parameters_does_not_mask_unexpected_errors(
    mock_sync_public_parameters,
    neo4j_session,
):
    # Act and assert
    with raises(RuntimeError, match="load failed"):
        cartography.intel.aws._sync_shared_public_ssm_parameters(
            neo4j_session,
            mock.MagicMock(),
            {"default": "111111111111"},
            ["ssm"],
            PUBLIC_SSM_JOB_PARAMETERS.copy(),
            configured_regions=["us-east-1"],
            aws_best_effort_mode=True,
        )

    mock_sync_public_parameters.assert_called_once()


@mock.patch.object(cartography.intel.aws.ssm_intel, "sync_public_parameters")
@mock.patch.object(cartography.intel.aws, "_autodiscover_account_regions")
@mock.patch.object(cartography.intel.aws, "_get_boto3_session_for_profile")
@mark.parametrize("allowlist", [None, "", ","])
def test_sync_shared_public_ssm_parameters_skips_aws_calls_when_disabled(
    mock_get_session,
    mock_autodiscover_regions,
    mock_sync_public_parameters,
    neo4j_session,
    allowlist,
):
    # Arrange
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "aws_ssm_public_parameter_prefix_allowlist": allowlist,
    }

    # Act
    cartography.intel.aws._sync_shared_public_ssm_parameters(
        neo4j_session,
        mock.MagicMock(),
        {"default": "111111111111"},
        ["ssm"],
        common_job_parameters,
        configured_regions=None,
        aws_best_effort_mode=False,
    )

    # Assert
    mock_get_session.assert_not_called()
    mock_autodiscover_regions.assert_not_called()
    mock_sync_public_parameters.assert_called_once_with(
        neo4j_session,
        {},
        TEST_UPDATE_TAG,
        common_job_parameters,
    )


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


def test_kms_syncs_before_kms_dependent_resources():
    """Resources that wire ENCRYPTED_BY edges by matching existing AWSKMSKey nodes
    (s3, rds, efs, dynamodb) must sync after kms, otherwise the edges are silently
    missed on a full sync."""
    order = list(RESOURCE_FUNCTIONS.keys())
    kms_index = order.index("kms")
    for dependent in ("s3", "rds", "efs", "dynamodb"):
        assert kms_index < order.index(dependent), (
            f"'kms' must sync before '{dependent}' so the ENCRYPTED_BY edge can "
            f"match existing AWSKMSKey nodes"
        )


def test_route53_syncs_after_its_dns_points_to_targets():
    """The route53 loader creates DNS_POINTS_TO by matching nodes that already exist, so the
    modules holding those nodes must sync first, otherwise the edges are silently missed and
    cleanup_route53 deletes the ones a previous run created."""
    order = list(RESOURCE_FUNCTIONS.keys())
    route53_index = order.index("route53")
    for dependency in (
        "ec2:load_balancer",
        "ec2:load_balancer_v2",
        "ec2:instance",
        "elastic_ip_addresses",
    ):
        assert order.index(dependency) < route53_index, (
            f"'{dependency}' must sync before 'route53' so its DNS_POINTS_TO edges can "
            f"match existing nodes"
        )


def test_route53_syncs_before_elasticsearch():
    """elasticsearch ingests its endpoint's DNS record with raw Cypher and its cleanup DETACH
    DELETEs any stale DNSRecord pointing at an AWSESDomain. If route53 ran first and attached
    its own record, that cleanup would delete the route53-owned node on every later run,
    before route53 re-stamps it."""
    order = list(RESOURCE_FUNCTIONS.keys())
    assert order.index("route53") < order.index("elasticsearch")


def test_standardize_aws_sync_kwargs():
    """
    Makes sure that we always use a standard set of parameter names for AWS syncs referenced in the
    cartography.intel.aws.resources.RESOURCE_FUNCTIONS function table. This standardization gives us
    flexibility when calling these syncs as function pointers.

    Fine print: this test excludes parameters with default values (e.g. `tag_resource_type_mappings` in
    resourcegroupstaggingapi).

    The set of standardized sync param names is maintained in
    tests.unit.cartography.intel.aws.test_init.make_aws_sync_test_kwargs.

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
                    f"tests.unit.cartography.intel.aws.test_init.make_aws_sync_test_kwargs."
                )
