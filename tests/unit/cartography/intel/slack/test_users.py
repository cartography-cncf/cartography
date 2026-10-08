from unittest.mock import Mock
from unittest.mock import patch

import pytest
from slack_sdk.errors import SlackApiError

from cartography.intel.slack.users import get_last_logins
from tests.data.slack.users import SLACK_ACCESS_LOGS


@patch(
    "cartography.intel.slack.users.slack_paginate",
    return_value=SLACK_ACCESS_LOGS["logins"],
)
def test_get_last_logins_keeps_latest_entry_per_user(mock_slack_paginate):
    # Arrange
    slack_client = Mock()

    # Act
    last_logins = get_last_logins(slack_client, "T123")

    # Assert
    assert last_logins == {"SLACKUSER1": 1767225600, "SLACKBOT1": 1767225600}
    mock_slack_paginate.assert_called_once_with(
        slack_client,
        "team_accessLogs",
        "logins",
        team_id="T123",
        limit=999,
    )


@pytest.mark.parametrize(
    "error_code",
    ["missing_scope", "not_allowed_token_type", "paid_only"],
)
@patch("cartography.intel.slack.users.slack_paginate")
def test_get_last_logins_skips_when_access_logs_unavailable(
    mock_slack_paginate,
    error_code,
):
    # Arrange
    mock_slack_paginate.side_effect = SlackApiError(
        "Failed to read access logs",
        {"error": error_code},
    )

    # Act
    last_logins = get_last_logins(Mock(), "T123")

    # Assert
    assert last_logins == {}


@patch("cartography.intel.slack.users.slack_paginate")
def test_get_last_logins_raises_unexpected_errors(mock_slack_paginate):
    # Arrange
    mock_slack_paginate.side_effect = SlackApiError(
        "Failed to read access logs",
        {"error": "invalid_auth"},
    )

    # Act / Assert
    with pytest.raises(SlackApiError):
        get_last_logins(Mock(), "T123")
