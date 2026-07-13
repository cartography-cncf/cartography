from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from botocore.exceptions import ConnectTimeoutError

from cartography.intel.aws import sagemaker
from cartography.intel.aws.sagemaker import notebook_instances
from cartography.intel.aws.sagemaker.util import SageMakerTransientRegionFailure


def _client_error(code: str, message: str, status_code: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": message},
            "ResponseMetadata": {"HTTPStatusCode": status_code},
        },
        "ListNotebookInstances",
    )


def test_get_notebook_instances_raises_transient_region_failure_on_timeout(mocker):
    boto3_session = MagicMock()
    client = MagicMock()
    client.get_paginator.return_value.paginate.side_effect = ConnectTimeoutError(
        endpoint_url="https://api.sagemaker.me-south-1.amazonaws.com",
    )
    mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.create_boto3_client",
        return_value=client,
    )

    with pytest.raises(SageMakerTransientRegionFailure):
        notebook_instances.get_notebook_instances(boto3_session, "me-south-1")


def test_get_notebook_instances_raises_transient_region_failure_on_retryable_client_error(
    mocker,
):
    boto3_session = MagicMock()
    client = MagicMock()
    client.get_paginator.return_value.paginate.side_effect = _client_error(
        "ServiceUnavailable",
        "Service unavailable",
        503,
    )
    mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.create_boto3_client",
        return_value=client,
    )

    with pytest.raises(SageMakerTransientRegionFailure):
        notebook_instances.get_notebook_instances(boto3_session, "me-south-1")


def test_get_notebook_instances_returns_empty_list_on_access_denied(mocker):
    boto3_session = MagicMock()
    client = MagicMock()
    client.get_paginator.return_value.paginate.side_effect = _client_error(
        "AccessDeniedException",
        "Access denied",
        403,
    )
    mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.create_boto3_client",
        return_value=client,
    )

    result = notebook_instances.get_notebook_instances(boto3_session, "me-south-1")

    assert result == []


def test_get_notebook_instances_returns_empty_list_on_unsupported_region_error(
    mocker,
):
    boto3_session = MagicMock()
    client = MagicMock()
    client.get_paginator.return_value.paginate.side_effect = _client_error(
        "UnknownOperationException",
        "This operation is not supported in this region.",
        400,
    )
    mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.create_boto3_client",
        return_value=client,
    )

    result = notebook_instances.get_notebook_instances(boto3_session, "me-south-1")

    assert result == []


def test_sync_notebook_instances_loads_healthy_regions_and_skips_cleanup_after_transient_failure(
    mocker,
):
    def _get_notebook_instances_side_effect(_, region):
        if region == "us-east-1":
            return [{"NotebookInstanceName": "nb-1"}]
        raise SageMakerTransientRegionFailure("temporary failure")

    get_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.get_notebook_instances",
        side_effect=_get_notebook_instances_side_effect,
    )
    transform_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.transform_notebook_instances",
        side_effect=lambda data, region: [{"Region": region, **item} for item in data],
    )
    load_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.load_notebook_instances",
    )
    cleanup_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.cleanup_notebook_instances",
    )

    failed_regions = notebook_instances.sync_notebook_instances(
        neo4j_session=MagicMock(),
        boto3_session=MagicMock(),
        regions=["us-east-1", "me-south-1"],
        current_aws_account_id="123456789012",
        aws_update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "AWS_ID": "123456789012"},
        skip_regions=set(),
    )

    assert failed_regions == {"me-south-1"}
    assert get_notebook_instances.call_count == 2
    transform_notebook_instances.assert_called_once_with(
        [{"NotebookInstanceName": "nb-1"}],
        "us-east-1",
    )
    load_notebook_instances.assert_called_once_with(
        mocker.ANY,
        [{"NotebookInstanceName": "nb-1", "Region": "us-east-1"}],
        "us-east-1",
        "123456789012",
        1,
    )
    cleanup_notebook_instances.assert_not_called()


def test_sync_notebook_instances_skips_cleanup_when_regions_are_already_marked_failed(
    mocker,
):
    get_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.get_notebook_instances",
        return_value=[{"NotebookInstanceName": "nb-1"}],
    )
    mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.transform_notebook_instances",
        side_effect=lambda data, region: data,
    )
    load_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.load_notebook_instances",
    )
    cleanup_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.notebook_instances.cleanup_notebook_instances",
    )

    failed_regions = notebook_instances.sync_notebook_instances(
        neo4j_session=MagicMock(),
        boto3_session=MagicMock(),
        regions=["us-east-1", "me-south-1"],
        current_aws_account_id="123456789012",
        aws_update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "AWS_ID": "123456789012"},
        skip_regions={"me-south-1"},
    )

    assert failed_regions == set()
    get_notebook_instances.assert_called_once_with(mocker.ANY, "us-east-1")
    load_notebook_instances.assert_called_once()
    cleanup_notebook_instances.assert_not_called()


def test_sagemaker_sync_filters_supported_regions_and_carries_skip_regions_forward(
    mocker,
):
    boto3_session = MagicMock()
    captured_skip_regions = {}
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = ["us-east-1", "me-south-1"]

    def _capture_skip_regions(name, return_value):
        def _side_effect(*args):
            captured_skip_regions.setdefault(name, []).append(args[6].copy())
            return return_value

        return _side_effect

    sync_notebook_instances = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_notebook_instances",
        side_effect=_capture_skip_regions(
            "notebook_instances",
            {"me-south-1"},
        ),
    )
    sync_domains = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_domains",
        side_effect=_capture_skip_regions("domains", set()),
    )
    sync_user_profiles = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_user_profiles",
        side_effect=_capture_skip_regions("user_profiles", set()),
    )
    sync_training_jobs = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_training_jobs",
        side_effect=_capture_skip_regions("training_jobs", set()),
    )
    sync_models = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_models",
        side_effect=_capture_skip_regions("models", set()),
    )
    sync_endpoint_configs = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_endpoint_configs",
        side_effect=_capture_skip_regions("endpoint_configs", set()),
    )
    sync_endpoints = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_endpoints",
        side_effect=_capture_skip_regions("endpoints", set()),
    )
    sync_transform_jobs = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_transform_jobs",
        side_effect=_capture_skip_regions("transform_jobs", set()),
    )
    sync_model_package_groups = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_model_package_groups",
        side_effect=_capture_skip_regions("model_package_groups", set()),
    )
    sync_model_packages = mocker.patch(
        "cartography.intel.aws.sagemaker.sync_model_packages",
        side_effect=_capture_skip_regions("model_packages", set()),
    )

    sagemaker.sync(
        neo4j_session=MagicMock(),
        boto3_session=boto3_session,
        regions=["us-east-1", "me-south-1", "eu-west-3"],
        current_aws_account_id="123456789012",
        update_tag=1,
        common_job_parameters={"UPDATE_TAG": 1, "AWS_ID": "123456789012"},
    )

    expected_regions = ["us-east-1", "me-south-1"]
    assert sync_notebook_instances.call_count == 1
    assert sync_notebook_instances.call_args.args[:6] == (
        mocker.ANY,
        boto3_session,
        expected_regions,
        "123456789012",
        1,
        {"UPDATE_TAG": 1, "AWS_ID": "123456789012"},
    )
    for patched_sync in (
        sync_domains,
        sync_user_profiles,
        sync_training_jobs,
        sync_models,
        sync_endpoint_configs,
        sync_endpoints,
        sync_transform_jobs,
        sync_model_package_groups,
        sync_model_packages,
    ):
        assert patched_sync.call_count == 1
        assert patched_sync.call_args.args[:6] == (
            mocker.ANY,
            boto3_session,
            expected_regions,
            "123456789012",
            1,
            {"UPDATE_TAG": 1, "AWS_ID": "123456789012"},
        )

    assert captured_skip_regions["notebook_instances"] == [set()]
    for name in (
        "domains",
        "user_profiles",
        "training_jobs",
        "models",
        "endpoint_configs",
        "endpoints",
        "transform_jobs",
        "model_package_groups",
        "model_packages",
    ):
        assert captured_skip_regions[name] == [{"me-south-1"}]
