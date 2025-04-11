from unittest.mock import MagicMock
from unittest.mock import patch

import botocore
import pytest

from cartography.intel.aws.ec2.launch_templates import get_launch_template_versions_by_template
from tests.utils import unwrapper


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
