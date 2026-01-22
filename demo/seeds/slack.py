from unittest.mock import Mock
from unittest.mock import patch

from slack_sdk import WebClient

import cartography.intel.slack.channels
import cartography.intel.slack.groups
import cartography.intel.slack.teams
import cartography.intel.slack.users
import tests.data.slack.channels
import tests.data.slack.teams
import tests.data.slack.usergroups
import tests.data.slack.users
from demo.seeds.base import Seed

SLACK_TOKEN = "fake-slack-token"


class SlackSeed(Seed):
    @patch.object(
        cartography.intel.slack.teams,
        "get_teams",
        return_value=tests.data.slack.teams.SLACK_TEAMS,
    )
    @patch.object(
        cartography.intel.slack.teams,
        "get_teams_details",
        return_value=[tests.data.slack.teams.SLACK_TEAMS_DETAILS["team"]],
    )
    @patch.object(
        cartography.intel.slack.users,
        "get",
        return_value=tests.data.slack.users.SLACK_USERS["members"],
    )
    @patch.object(
        cartography.intel.slack.channels,
        "get",
        return_value=tests.data.slack.channels.SLACK_CHANNELS["channels"],
    )
    @patch.object(
        cartography.intel.slack.groups,
        "get",
        return_value=tests.data.slack.usergroups.SLACK_USERGROUPS["usergroups"],
    )
    def seed(self, *args) -> None:
        # Create a mock Slack client
        mock_slack_client = Mock(spec=WebClient)

        common_job_parameters = {
            "UPDATE_TAG": self.update_tag,
            "CHANNELS_MEMBERSHIPS": False,
        }

        self._seed_teams(mock_slack_client, common_job_parameters)
        self._seed_users(mock_slack_client, common_job_parameters)
        self._seed_channels(mock_slack_client, common_job_parameters)
        self._seed_groups(mock_slack_client, common_job_parameters)

    def _seed_teams(self, slack_client: Mock, common_job_parameters: dict) -> None:
        team_ids = cartography.intel.slack.teams.sync(
            self.neo4j_session,
            slack_client,
            self.update_tag,
            common_job_parameters,
        )
        # Store for use in other seed methods
        common_job_parameters["TEAM_IDS"] = team_ids

    def _seed_users(self, slack_client: Mock, common_job_parameters: dict) -> None:
        for team_id in common_job_parameters["TEAM_IDS"]:
            common_job_parameters["TEAM_ID"] = team_id
            cartography.intel.slack.users.sync(
                self.neo4j_session,
                slack_client,
                team_id,
                self.update_tag,
                common_job_parameters,
            )

    def _seed_channels(self, slack_client: Mock, common_job_parameters: dict) -> None:
        for team_id in common_job_parameters["TEAM_IDS"]:
            common_job_parameters["TEAM_ID"] = team_id
            cartography.intel.slack.channels.sync(
                self.neo4j_session,
                slack_client,
                team_id,
                self.update_tag,
                common_job_parameters,
            )

    def _seed_groups(self, slack_client: Mock, common_job_parameters: dict) -> None:
        for team_id in common_job_parameters["TEAM_IDS"]:
            common_job_parameters["TEAM_ID"] = team_id
            cartography.intel.slack.groups.sync(
                self.neo4j_session,
                slack_client,
                team_id,
                self.update_tag,
                common_job_parameters,
            )
