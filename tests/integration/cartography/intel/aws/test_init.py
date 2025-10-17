import inspect
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from unittest import mock

import neo4j
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
@mock.patch.object(cartography.intel.aws, "_autodiscover_accounts", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job", return_value=None)
def test_sync_multiple_accounts(
    mock_cleanup,
    mock_autodiscover,
    mock_sync_one,
    mock_boto3_session,
    mock_aioboto3_session,
    mock_sync_orgs,
    neo4j_session,
):
    test_config = cartography.config.Config(
        neo4j_uri="bolt://localhost:7687",
    )
    cartography.intel.aws._sync_multiple_accounts(
        neo4j_session,
        TEST_ACCOUNTS,
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        test_config,
    )

    # Ensure we call _sync_one_account on all accounts in our list.
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(),
        "000000000000",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(),
    )
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(),
        "000000000001",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(),
    )
    mock_sync_one.assert_any_call(
        neo4j_session,
        mock_boto3_session(),
        "000000000002",
        TEST_UPDATE_TAG,
        GRAPH_JOB_PARAMETERS,
        regions=None,
        aws_requested_syncs=[],
        aioboto3_session=mock_aioboto3_session(),
    )

    # Ensure _sync_one_account and _autodiscover is called once for each account
    assert mock_sync_one.call_count == len(TEST_ACCOUNTS.keys())
    assert mock_autodiscover.call_count == len(TEST_ACCOUNTS.keys())

    # This is a brittle test, but it is here to ensure that the mock_cleanup path is correct.
    assert mock_cleanup.call_count == 1


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
    )

    # Act
    cartography.intel.aws.start_aws_ingestion(neo4j_session, test_config)

    # Assert
    assert mock_sync_multiple.call_count == 1
    mock_perform_analysis.assert_called_once_with(
        list(RESOURCE_FUNCTIONS.keys()),
        neo4j_session,
        {
            "UPDATE_TAG": test_config.update_tag,
            "permission_relationships_file": test_config.permission_relationships_file,
            "aws_guardduty_severity_threshold": None,
            "aws_cloudtrail_management_events_lookback_hours": test_config.aws_cloudtrail_management_events_lookback_hours,
            "experimental_aws_inspector_batch": test_config.experimental_aws_inspector_batch,
        },
    )


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations.get_aws_accounts_from_botocore_config")
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job")
def test_start_aws_ingestion_raises_aggregated_exceptions_with_aws_best_effort_mode(
    mock_run_cleanup_job,
    mock_perform_analysis,
    mock_sync_one,
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
    assert mock_run_cleanup_job.call_count == 0
    assert mock_perform_analysis.call_count == 0


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations.get_aws_accounts_from_botocore_config")
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job")
def test_start_aws_ingestion_raises_one_exception_without_aws_best_effort_mode(
    mock_run_cleanup_job,
    mock_perform_analysis,
    mock_sync_one,
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
    assert mock_run_cleanup_job.call_count == 0
    assert mock_perform_analysis.call_count == 0


@mock.patch("cartography.intel.aws.aioboto3.Session")
@mock.patch("cartography.intel.aws.boto3.Session")
@mock.patch("cartography.intel.aws.organizations.get_aws_accounts_from_botocore_config")
@mock.patch.object(cartography.intel.aws, "_sync_one_account", return_value=None)
@mock.patch.object(cartography.intel.aws, "_perform_aws_analysis", return_value=None)
@mock.patch.object(cartography.intel.aws, "run_cleanup_job")
def test_start_aws_ingestion_does_cleanup(
    mock_run_cleanup_job,
    mock_perform_analysis,
    mock_sync_one,
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
    assert mock_analysis.call_count == 1


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
