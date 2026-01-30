from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import botocore
import pytest

from cartography.intel.aws.ec2.launch_templates import (
    get_launch_template_versions_by_template,
)
from cartography.intel.aws.ec2.launch_templates import transform_launch_templates
from tests.utils import unwrapper

FAKE_AWS_ACCOUNT_ID = "123456789012"
FAKE_REGION = "us-east-1"
FAKE_UPDATE_TAG = 123456789
COMMON_JOB_PARAMS = {"AWS_ID": FAKE_AWS_ACCOUNT_ID, "Region": FAKE_REGION}
MOCK_CREATE_TIME_DT = datetime(2023, 1, 1, 0, 0, 0)
MOCK_CREATE_TIME_STR = str(int(MOCK_CREATE_TIME_DT.timestamp()))


@patch("cartography.intel.aws.ec2.launch_templates.logger")
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
        error_response={
            "Error": {
                "Code": "InvalidLaunchTemplateId.NotFound",
                "Message": "Launch template not found",
            }
        },
        operation_name="DescribeLaunchTemplateVersions",
    )

    # Act
    result = get_launch_template_versions_by_template(
        mock_session,
        "fake-template-id",
        "us-east-1",
    )

    # Assert
    assert result == []
    mock_logger.warning.assert_called_once_with(
        "Launch template %s no longer exists in region %s",
        "fake-template-id",
        "us-east-1",
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
        error_response={
            "Error": {"Code": "ValidationError", "Message": "Validation error"}
        },
        operation_name="DescribeLaunchTemplateVersions",
    )

    # Unwrap the function to bypass retry logic
    original_func = unwrapper(get_launch_template_versions_by_template)

    # Act & Assert
    with pytest.raises(botocore.exceptions.ClientError):
        original_func(
            mock_session,
            "fake-template-id",
            "us-east-1",
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
    mock_template_version = {"LaunchTemplateVersions": [{"VersionNumber": 1}]}
    mock_paginator.paginate.return_value = [mock_template_version]

    # Act
    result = get_launch_template_versions_by_template(
        mock_session,
        "valid-template-id",
        "us-east-1",
    )

    # Assert
    assert result == [{"VersionNumber": 1}]
    mock_client.get_paginator.assert_called_once_with(
        "describe_launch_template_versions"
    )
    mock_paginator.paginate.assert_called_once_with(
        LaunchTemplateId="valid-template-id"
    )


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
        "",
        "us-east-1",
    )

    # Assert
    assert result_versions == []


def test_transform_launch_templates_no_matching_ids():
    """
    Test that the function returns an empty list when no template IDs match version IDs.
    """
    # Arrange
    templates = [
        {
            "LaunchTemplateId": "lt-123456",
            "CreateTime": MOCK_CREATE_TIME_DT,
            "LaunchTemplateName": "template1",
        },
    ]
    versions = [
        {
            "LaunchTemplateId": "lt-789012",
            "VersionNumber": 1,
        },
    ]

    # Act
    result = transform_launch_templates(templates, versions)

    # Assert
    assert result == []


def test_transform_launch_templates_multiple_matches():
    """
    Test that the function correctly transforms multiple templates with matching version IDs.
    """
    # Arrange
    templates = [
        {
            "LaunchTemplateId": "lt-123456",
            "CreateTime": MOCK_CREATE_TIME_DT,
            "LaunchTemplateName": "template1",
        },
        {
            "LaunchTemplateId": "lt-789012",
            "CreateTime": MOCK_CREATE_TIME_DT,
            "LaunchTemplateName": "template2",
        },
    ]
    versions = [
        {
            "LaunchTemplateId": "lt-123456",
            "VersionNumber": 1,
        },
        {
            "LaunchTemplateId": "lt-789012",
            "VersionNumber": 1,
        },
    ]

    # Act
    result = transform_launch_templates(templates, versions)

    # Assert
    assert len(result) == 2
    assert result[0]["LaunchTemplateId"] == "lt-123456"
    assert result[0]["CreateTime"] == MOCK_CREATE_TIME_STR
    assert result[1]["LaunchTemplateId"] == "lt-789012"
    assert result[1]["CreateTime"] == MOCK_CREATE_TIME_STR


def test_transform_launch_templates_preserves_other_fields():
    """
    Test that the function preserves all other fields in the template.
    """
    # Arrange
    templates = [
        {
            "LaunchTemplateId": "lt-123456",
            "CreateTime": MOCK_CREATE_TIME_DT,
            "LaunchTemplateName": "template1",
            "CreatedBy": "user1",
            "DefaultVersionNumber": 1,
            "LatestVersionNumber": 2,
        },
    ]
    versions = [
        {
            "LaunchTemplateId": "lt-123456",
            "VersionNumber": 1,
        },
    ]

    # Act
    result = transform_launch_templates(templates, versions)

    # Assert
    assert len(result) == 1
    assert result[0]["LaunchTemplateId"] == "lt-123456"
    assert result[0]["LaunchTemplateName"] == "template1"
    assert result[0]["CreatedBy"] == "user1"
    assert result[0]["DefaultVersionNumber"] == 1
    assert result[0]["LatestVersionNumber"] == 2
    assert result[0]["CreateTime"] == MOCK_CREATE_TIME_STR
