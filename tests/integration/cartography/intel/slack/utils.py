from collections import namedtuple
from unittest.mock import Mock

import tests.data.slack.channels
import tests.data.slack.teams
import tests.data.slack.usergroups
import tests.data.slack.users

DataResult = namedtuple("DataResult", ["data"])


slack_client = Mock(
    auth_teams_list=Mock(
        return_value=DataResult(data=tests.data.slack.teams.SLACK_TEAMS)
    ),
    team_info=Mock(
        return_value=DataResult(data=tests.data.slack.teams.SLACK_TEAMS_DETAILS)
    ),
    users_list=Mock(return_value=tests.data.slack.users.SLACK_USERS),
    conversations_list=Mock(return_value=tests.data.slack.channels.SLACK_CHANNELS),
    conversations_members=Mock(
        return_value=tests.data.slack.channels.SLACK_CHANNELS_MEMBERSHIPS
    ),
    usergroups_list=Mock(return_value=tests.data.slack.usergroups.SLACK_USERGROUPS),
)
