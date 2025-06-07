from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.users
import cartography.intel.anthropic.workspaces
import tests.data.anthropic.apikeys
import tests.data.anthropic.users
import tests.data.anthropic.workspaces
from demo.seeds.base import Seed

ORG_ID = "8834c225-ea27-405a-aea9-5ed5f07f4858"


class AnthropicSeed(Seed):
    @patch.object(
        cartography.intel.anthropic.workspaces,
        "get_workspace_users",
        return_value=tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES_MEMBERS,
    )
    @patch.object(
        cartography.intel.anthropic.workspaces,
        "get",
        return_value=(ORG_ID, tests.data.anthropic.workspaces.ANTHROPIC_WORKSPACES),
    )
    @patch.object(
        cartography.intel.anthropic.users,
        "get",
        return_value=(ORG_ID, tests.data.anthropic.users.ANTHROPIC_USERS),
    )
    @patch.object(
        cartography.intel.anthropic.apikeys,
        "get",
        return_value=(ORG_ID, tests.data.anthropic.apikeys.ANTHROPIC_APIKEYS),
    )
    def seed(self, *args) -> None:
        api_session = Mock()
        self._seed_users(api_session)
        self._seed_workspaces(api_session)
        self._seed_apikeys(api_session)

    def _seed_users(self, api_session: Mock) -> None:
        cartography.intel.anthropic.users.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.anthropic.com/v1",
            },
        )

    def _seed_workspaces(self, api_session: Mock) -> list[dict]:
        return cartography.intel.anthropic.workspaces.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.anthropic.com/v1",
            },
        )

    def _seed_apikeys(self, api_session: Mock) -> None:
        cartography.intel.anthropic.apikeys.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.anthropic.com/v1",
            },
        )
