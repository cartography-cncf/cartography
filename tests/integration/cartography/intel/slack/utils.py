from collections import namedtuple
from typing import Any
from unittest.mock import Mock

import tests.data.slack.channels
import tests.data.slack.teams
import tests.data.slack.usergroups
import tests.data.slack.users

DataResult = namedtuple("DataResult", ["data"])


def _conversations_list(**kwargs: Any) -> dict[str, Any]:
    """
    Emulate Slack's server-side filtering of `conversations.list` on `types`, which
    defaults to `public_channel` only. Without this, a mock that ignores kwargs would
    hand back private channels even when the caller never asked for them.
    """
    requested_types = set(kwargs.get("types", "public_channel").split(","))
    channels = [
        channel
        for channel in tests.data.slack.channels.SLACK_CHANNELS["channels"]
        if ("private_channel" if channel["is_private"] else "public_channel")
        in requested_types
    ]
    return {"channels": channels}


slack_client = Mock(
    auth_teams_list=Mock(
        return_value=DataResult(data=tests.data.slack.teams.SLACK_TEAMS)
    ),
    team_info=Mock(
        return_value=DataResult(data=tests.data.slack.teams.SLACK_TEAMS_DETAILS)
    ),
    users_list=Mock(return_value=tests.data.slack.users.SLACK_USERS),
    conversations_list=Mock(side_effect=_conversations_list),
    conversations_members=Mock(
        return_value=tests.data.slack.channels.SLACK_CHANNELS_MEMBERSHIPS
    ),
    usergroups_list=Mock(return_value=tests.data.slack.usergroups.SLACK_USERGROUPS),
)
