from unittest.mock import Mock
from unittest.mock import patch

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
