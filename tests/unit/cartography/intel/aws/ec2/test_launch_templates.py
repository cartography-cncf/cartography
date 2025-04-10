from unittest.mock import MagicMock
from unittest.mock import patch

import botocore
import pytest

from cartography.intel.aws.ec2.launch_templates import get_launch_template_versions
from cartography.intel.aws.ec2.launch_templates import get_launch_template_versions_by_template
from tests.utils import unwrapper


@patch('cartography.intel.aws.ec2.launch_templates.logger')
def test_get_launch_template_versions_by_template_not_found(mock_logger):
    """
    Test that a ClientError with code 'InvalidLaunchTemplateId.NotFound' is raised
    when the template is not found.
    """
    # Arrange
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_paginator = MagicMock()
    mock_session.client.return_value = mock_client
    mock_client.get_paginator.return_value = mock_paginator
    not_found_error = botocore.exceptions.ClientError(
        error_response={'Error': {'Code': 'InvalidLaunchTemplateId.NotFound', 'Message': 'Launch template not found'}},
        operation_name='DescribeLaunchTemplateVersions',
    )
    mock_paginator.paginate.side_effect = not_found_error

    # Unwrap the function because we removed @aws_handle_regions
    original_func = unwrapper(get_launch_template_versions_by_template)

    # Act & Assert
    with pytest.raises(botocore.exceptions.ClientError) as excinfo:
        original_func(
            mock_session,
            'fake-template-id',
            'us-east-1',
        )

    # Check if the raised exception is the one we expect
    assert excinfo.value is not_found_error
    # Ensure no warning was logged here, as it now happens in the caller
    mock_logger.warning.assert_not_called()


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


@patch('cartography.intel.aws.ec2.launch_templates.get_launch_template_versions_by_template')
def test_get_launch_template_versions_all_found(mock_get_by_template):
    """
    Test that when all templates have versions, the function returns all versions and all original templates.
    """
    # Arrange
    mock_session = MagicMock()
    region = 'us-west-2'
    templates = [
        {'LaunchTemplateId': 'lt-1'},
        {'LaunchTemplateId': 'lt-2'},
    ]
    versions_lt1 = [{'VersionNumber': 1, 'LaunchTemplateId': 'lt-1'}]
    versions_lt2 = [{'VersionNumber': 1, 'LaunchTemplateId': 'lt-2'}, {'VersionNumber': 2, 'LaunchTemplateId': 'lt-2'}]
    mock_get_by_template.side_effect = [versions_lt1, versions_lt2]

    # Act
    result_versions, result_templates = get_launch_template_versions(mock_session, region, templates)

    # Assert
    assert result_versions == versions_lt1 + versions_lt2
    assert result_templates == templates
    assert mock_get_by_template.call_count == 2
    mock_get_by_template.assert_any_call(mock_session, 'lt-1', region)
    mock_get_by_template.assert_any_call(mock_session, 'lt-2', region)


@patch('cartography.intel.aws.ec2.launch_templates.logger')
@patch('cartography.intel.aws.ec2.launch_templates.get_launch_template_versions_by_template')
def test_get_launch_template_versions_some_not_found(mock_get_by_template, mock_logger):
    """
    Test that when some templates are not found (raising ClientError), the function logs a warning
    """
    # Arrange
    mock_session = MagicMock()
    region = 'us-east-1'
    templates = [
        {'LaunchTemplateId': 'lt-found'},
        {'LaunchTemplateId': 'lt-not-found'},
        {'LaunchTemplateId': 'lt-also-found'},
    ]
    versions_found = [{'VersionNumber': 1, 'LaunchTemplateId': 'lt-found'}]
    versions_also_found = [{'VersionNumber': 3, 'LaunchTemplateId': 'lt-also-found'}]
    # Simulate 'lt-not-found' raising ClientError
    not_found_error = botocore.exceptions.ClientError(
        error_response={'Error': {'Code': 'InvalidLaunchTemplateId.NotFound', 'Message': 'Not Found'}},
        operation_name='DescribeLaunchTemplateVersions',
    )
    mock_get_by_template.side_effect = [versions_found, not_found_error, versions_also_found]

    # Act
    result_versions, result_templates = get_launch_template_versions(mock_session, region, templates)

    # Assert
    assert result_versions == versions_found + versions_also_found
    assert result_templates == [
        {'LaunchTemplateId': 'lt-found'},
        {'LaunchTemplateId': 'lt-also-found'},
    ]
    assert mock_get_by_template.call_count == 3
    mock_get_by_template.assert_any_call(mock_session, 'lt-found', region)
    mock_get_by_template.assert_any_call(mock_session, 'lt-not-found', region)
    mock_get_by_template.assert_any_call(mock_session, 'lt-also-found', region)
    mock_logger.warning.assert_called_once_with(
        "Launch template %s no longer exists in region %s, skipping.",
        'lt-not-found', region,
    )


@patch('cartography.intel.aws.ec2.launch_templates.logger')
@patch('cartography.intel.aws.ec2.launch_templates.get_launch_template_versions_by_template')
def test_get_launch_template_versions_none_found(mock_get_by_template, mock_logger):
    """
    Test that when no templates are found (all raise ClientError), the function logs warnings
    """
    # Arrange
    mock_session = MagicMock()
    region = 'eu-central-1'
    templates = [
        {'LaunchTemplateId': 'lt-gone-1'},
        {'LaunchTemplateId': 'lt-gone-2'},
    ]
    # Simulate all templates raising ClientError
    not_found_error = botocore.exceptions.ClientError(
        error_response={'Error': {'Code': 'InvalidLaunchTemplateId.NotFound', 'Message': 'Not Found'}},
        operation_name='DescribeLaunchTemplateVersions',
    )
    mock_get_by_template.side_effect = not_found_error

    # Act
    result_versions, result_templates = get_launch_template_versions(mock_session, region, templates)

    # Assert
    assert result_versions == []
    assert result_templates == []
    assert mock_get_by_template.call_count == 2
    mock_get_by_template.assert_any_call(mock_session, 'lt-gone-1', region)
    mock_get_by_template.assert_any_call(mock_session, 'lt-gone-2', region)
    assert mock_logger.warning.call_count == 2
    mock_logger.warning.assert_any_call(
        "Launch template %s no longer exists in region %s, skipping.",
        'lt-gone-1', region,
    )
    mock_logger.warning.assert_any_call(
        "Launch template %s no longer exists in region %s, skipping.",
        'lt-gone-2', region,
    )


def test_get_launch_template_versions_empty_input():
    """
    Test that providing an empty list of templates results in empty output lists.
    """
    # Arrange
    mock_session = MagicMock()
    region = 'ap-southeast-2'
    templates = []

    # Act
    result_versions, result_templates = get_launch_template_versions(mock_session, region, templates)

    # Assert
    assert result_versions == []
    assert result_templates == []
