from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from slack_sdk.errors import SlackApiError

from cartography.intel.slack.channels import get


@patch("cartography.intel.slack.channels.slack_paginate", return_value=[])
def test_get_requests_public_and_private_channels(mock_slack_paginate):
    # Arrange
    slack_client = Mock()

    # Act
    channels = get(slack_client, "T123", False)

    # Assert
    assert channels == []
    mock_slack_paginate.assert_called_once_with(
        slack_client,
        "conversations_list",
        "channels",
        team_id="T123",
        exclude_archived=True,
        types="public_channel,private_channel",
    )


@pytest.mark.parametrize("error_code", ["invalid_types", "missing_scope"])
@patch("cartography.intel.slack.channels.slack_paginate")
def test_get_falls_back_to_public_channels(mock_slack_paginate, error_code):
    # Arrange
    slack_client = Mock()
    public_channel = {"id": "C123", "name": "public-channel"}
    mock_slack_paginate.side_effect = [
        SlackApiError("Failed to list channels", {"error": error_code}),
        [public_channel],
    ]

    # Act
    channels = get(slack_client, "T123", False)

    # Assert
    assert channels == [public_channel]
    assert mock_slack_paginate.call_args_list == [
        call(
            slack_client,
            "conversations_list",
            "channels",
            team_id="T123",
            exclude_archived=True,
            types="public_channel,private_channel",
        ),
        call(
            slack_client,
            "conversations_list",
            "channels",
            team_id="T123",
            exclude_archived=True,
            types="public_channel",
        ),
    ]


@patch("cartography.intel.slack.channels.slack_paginate")
def test_get_raises_unexpected_slack_errors(mock_slack_paginate):
    # Arrange
    slack_client = Mock()
    mock_slack_paginate.side_effect = SlackApiError(
        "Failed to list channels",
        {"error": "invalid_auth"},
    )

    # Act and assert
    with pytest.raises(SlackApiError):
        get(slack_client, "T123", False)
