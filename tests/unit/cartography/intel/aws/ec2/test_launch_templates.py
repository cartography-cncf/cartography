from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import botocore
import pytest

from cartography.intel.aws.ec2.launch_templates import get_launch_template_versions_by_template
from cartography.intel.aws.ec2.launch_templates import sync_ec2_launch_templates
from tests.utils import unwrapper

FAKE_AWS_ACCOUNT_ID = '123456789012'
FAKE_REGION = 'us-east-1'
FAKE_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {'AWS_ID': FAKE_AWS_ACCOUNT_ID, 'Region': FAKE_REGION}
MOCK_CREATE_TIME_DT = datetime(2023, 1, 1, 0, 0, 0)
MOCK_CREATE_TIME_STR = str(int(MOCK_CREATE_TIME_DT.timestamp()))


@patch('cartography.intel.aws.ec2.launch_templates.logger')
def test_get_launch_template_versions_by_template_not_found(mock_logger):
    """
    Test that a ClientError with code 'InvalidLaunchTemplateId.NotFound' logs a warning
    but doesn't raise an exception.
    """
    # Arrange
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.side_effect = botocore.exceptions.ClientError(
        error_response={'Error': {'Code': 'InvalidLaunchTemplateId.NotFound', 'Message': 'Launch template not found'}},
        operation_name='DescribeLaunchTemplateVersions',
    )

    # Act
    result = get_launch_template_versions_by_template(
        mock_session,
        'fake-template-id',
        'us-east-1',
    )

    # Assert
    assert result == []
    mock_logger.warning.assert_called_once_with(
        "Launch template %s no longer exists in region %s",
        'fake-template-id',
        'us-east-1',
    )


def test_get_launch_template_versions_by_template_other_error():
    """
    Test that a ClientError with any other code is re-raised.
    """
    # Arrange
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.side_effect = botocore.exceptions.ClientError(
        error_response={'Error': {'Code': 'ValidationError', 'Message': 'Validation error'}},
        operation_name='DescribeLaunchTemplateVersions',
    )

    # Unwrap the function to bypass retry logic
    original_func = unwrapper(get_launch_template_versions_by_template)

    # Act & Assert
    with pytest.raises(botocore.exceptions.ClientError):
        original_func(
            mock_session,
            'fake-template-id',
            'us-east-1',
        )


def test_get_launch_template_versions_by_template_success():
    """
    Test successful API call returns template versions.
    """
    # Arrange
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_template_version = {'LaunchTemplateVersions': [{'VersionNumber': 1}]}
    mock_paginator.paginate.return_value = [mock_template_version]

    # Act
    result = get_launch_template_versions_by_template(
        mock_session,
        'valid-template-id',
        'us-east-1',
    )

    # Assert
    assert result == [{'VersionNumber': 1}]
    mock_client.get_paginator.assert_called_once_with('describe_launch_template_versions')
    mock_paginator.paginate.assert_called_once_with(LaunchTemplateId='valid-template-id')


def test_get_launch_template_versions_empty_input():
    """
    Test that the function returns an empty list when given an empty input.
    """
    # Arrange
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    mock_paginator.paginate.return_value = []

    # Act
    result_versions = get_launch_template_versions_by_template(
        mock_session,
        '',
        'us-east-1',
    )

    # Assert
    assert result_versions == []


@patch('cartography.intel.aws.ec2.launch_templates.logger')
@patch('cartography.intel.aws.ec2.launch_templates.cleanup')
@patch('cartography.intel.aws.ec2.launch_templates.load_launch_template_versions')
@patch('cartography.intel.aws.ec2.launch_templates.transform_launch_template_versions')
@patch('cartography.intel.aws.ec2.launch_templates.load_launch_templates')
@patch('cartography.intel.aws.ec2.launch_templates.transform_launch_templates')
@patch('cartography.intel.aws.ec2.launch_templates.get_launch_template_versions')
@patch('cartography.intel.aws.ec2.launch_templates.get_launch_templates')
def test_sync_ec2_launch_templates_success(
    mock_get_templates, mock_get_versions, mock_transform_templates, mock_load_templates,
    mock_transform_versions, mock_load_versions, mock_cleanup, mock_logger,
):
    """
    Test sync function runs successfully, calling downstream functions with expected data.
    """
    # Arrange
    mock_neo4j_session = MagicMock()
    mock_boto3_session = MagicMock()
    regions = [FAKE_REGION]

    # Mock return values
    templates_raw = [{'LaunchTemplateId': 'lt-1', 'DefaultVersionNumber': 1, 'CreateTime': MOCK_CREATE_TIME_DT}]
    versions_raw = [{
        'LaunchTemplateId': 'lt-1',
        'VersionNumber': 1,
        'CreateTime': MOCK_CREATE_TIME_DT,
    }]
    found_templates_filtered = templates_raw

    # Transformed data needs CreateTime as string timestamp
    templates_transformed = [
        {'LaunchTemplateId': 'lt-1', 'DefaultVersionNumber': 1, 'CreateTime': MOCK_CREATE_TIME_STR},
    ]
    # Transformed data needs Id, CreateTime as string timestamp, and flattened LaunchTemplateData fields
    versions_transformed = [{
        'LaunchTemplateId': 'lt-1',
        'VersionNumber': 1,
        'Id': 'lt-1-1',
        'CreateTime': MOCK_CREATE_TIME_STR,
    }]

    mock_get_templates.return_value = templates_raw
    mock_get_versions.return_value = versions_raw
    mock_transform_templates.return_value = templates_transformed
    mock_transform_versions.return_value = versions_transformed

    # Act
    sync_ec2_launch_templates(
        mock_neo4j_session, mock_boto3_session, regions, FAKE_AWS_ACCOUNT_ID,
        FAKE_UPDATE_TAG, COMMON_JOB_PARAMS,
    )

    # Assert
    mock_get_templates.assert_called_once_with(mock_boto3_session, FAKE_REGION)
    mock_get_versions.assert_called_once_with(mock_boto3_session, FAKE_REGION, templates_raw)
    mock_transform_templates.assert_called_once_with(found_templates_filtered)
    mock_load_templates.assert_called_once_with(
        mock_neo4j_session, templates_transformed, FAKE_REGION, FAKE_AWS_ACCOUNT_ID, FAKE_UPDATE_TAG,
    )
    mock_transform_versions.assert_called_once_with(versions_raw)
    mock_load_versions.assert_called_once_with(
        mock_neo4j_session, versions_transformed, FAKE_REGION, FAKE_AWS_ACCOUNT_ID, FAKE_UPDATE_TAG,
    )
    mock_cleanup.assert_called_once_with(mock_neo4j_session, COMMON_JOB_PARAMS)
    mock_logger.info.assert_called_once_with(
        f"Syncing launch templates for region '{FAKE_REGION}' in account '{FAKE_AWS_ACCOUNT_ID}'.",
    )


@patch('cartography.intel.aws.ec2.launch_templates.logger')
@patch('cartography.intel.aws.ec2.launch_templates.cleanup')
@patch('cartography.intel.aws.ec2.launch_templates.load_launch_template_versions')
@patch('cartography.intel.aws.ec2.launch_templates.transform_launch_template_versions')
@patch('cartography.intel.aws.ec2.launch_templates.load_launch_templates')
@patch('cartography.intel.aws.ec2.launch_templates.transform_launch_templates')
@patch('cartography.intel.aws.ec2.launch_templates.get_launch_template_versions')
@patch('cartography.intel.aws.ec2.launch_templates.get_launch_templates')
def test_sync_ec2_launch_templates_template_not_found(
    mock_get_templates, mock_get_versions, mock_transform_templates, mock_load_templates,
    mock_transform_versions, mock_load_versions, mock_cleanup, mock_logger,
):
    """
    Test sync function when a template is not found during version fetch,
    ensuring it's filtered out before transform/load.
    """
    # Arrange
    mock_neo4j_session = MagicMock()
    mock_boto3_session = MagicMock()
    regions = [FAKE_REGION]

    # Mock return values
    templates_raw = [
        {'LaunchTemplateId': 'lt-not-found', 'DefaultVersionNumber': 1, 'CreateTime': MOCK_CREATE_TIME_DT},
        {'LaunchTemplateId': 'lt-1', 'DefaultVersionNumber': 1, 'CreateTime': MOCK_CREATE_TIME_DT},
    ]
    versions_raw = [{
        'LaunchTemplateId': 'lt-1',
        'VersionNumber': 1,
        'CreateTime': MOCK_CREATE_TIME_DT,
    }]
    found_templates_filtered = [
        {'LaunchTemplateId': 'lt-1', 'DefaultVersionNumber': 1, 'CreateTime': MOCK_CREATE_TIME_DT},
    ]
    templates_transformed = [
        {'LaunchTemplateId': 'lt-1', 'DefaultVersionNumber': 1, 'CreateTime': MOCK_CREATE_TIME_STR},
    ]
    versions_transformed = [{
        'LaunchTemplateId': 'lt-1',
        'VersionNumber': 1,
        'Id': 'lt-1-1',
        'CreateTime': MOCK_CREATE_TIME_STR,
    }]
    mock_get_templates.return_value = templates_raw
    mock_get_versions.return_value = versions_raw
    mock_transform_templates.return_value = templates_transformed
    mock_transform_versions.return_value = versions_transformed

    # Act
    sync_ec2_launch_templates(
        mock_neo4j_session, mock_boto3_session, regions, FAKE_AWS_ACCOUNT_ID,
        FAKE_UPDATE_TAG, COMMON_JOB_PARAMS,
    )

    # Assert
    mock_get_templates.assert_called_once_with(mock_boto3_session, FAKE_REGION)
    mock_get_versions.assert_called_once_with(mock_boto3_session, FAKE_REGION, templates_raw)

    # Crucially, assert transform/load are called with the *filtered* lists
    mock_transform_templates.assert_called_once_with(found_templates_filtered)
    mock_load_templates.assert_called_once_with(
        mock_neo4j_session, templates_transformed, FAKE_REGION, FAKE_AWS_ACCOUNT_ID, FAKE_UPDATE_TAG,
    )
    mock_transform_versions.assert_called_once_with(versions_raw)
    mock_load_versions.assert_called_once_with(
        mock_neo4j_session, versions_transformed, FAKE_REGION, FAKE_AWS_ACCOUNT_ID, FAKE_UPDATE_TAG,
    )

    mock_cleanup.assert_called_once_with(mock_neo4j_session, COMMON_JOB_PARAMS)
    mock_logger.info.assert_called_once_with(
        f"Syncing launch templates for region '{FAKE_REGION}' in account '{FAKE_AWS_ACCOUNT_ID}'.",
    )
