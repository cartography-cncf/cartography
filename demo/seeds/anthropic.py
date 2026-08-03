from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.anthropic.apikeys
import cartography.intel.anthropic.federation
import cartography.intel.anthropic.organization
import cartography.intel.anthropic.serviceaccounts
import cartography.intel.anthropic.users
import cartography.intel.anthropic.workspaces
import tests.data.anthropic.apikeys
import tests.data.anthropic.federation
import tests.data.anthropic.organization
import tests.data.anthropic.serviceaccounts
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
    @patch.object(
        cartography.intel.anthropic.organization,
        "get",
        return_value=tests.data.anthropic.organization.ANTHROPIC_ORGANIZATION,
    )
    @patch.object(
        cartography.intel.anthropic.serviceaccounts,
        "get_service_account_workspaces",
        side_effect=lambda _session, _url, service_account_id: (
            tests.data.anthropic.serviceaccounts.ANTHROPIC_SERVICE_ACCOUNT_WORKSPACES[
                service_account_id
            ]
        ),
    )
    @patch.object(
        cartography.intel.anthropic.serviceaccounts,
        "get",
        return_value=tests.data.anthropic.serviceaccounts.ANTHROPIC_SERVICE_ACCOUNTS,
    )
    @patch.object(
        cartography.intel.anthropic.federation,
        "get_rule_workspaces",
        side_effect=lambda _session, _url, rule_id: (
            tests.data.anthropic.federation.ANTHROPIC_FEDERATION_RULE_WORKSPACES[
                rule_id
            ]
        ),
    )
    @patch.object(
        cartography.intel.anthropic.federation,
        "get_rules",
        return_value=tests.data.anthropic.federation.ANTHROPIC_FEDERATION_RULES,
    )
    @patch.object(
        cartography.intel.anthropic.federation,
        "get_issuers",
        return_value=tests.data.anthropic.federation.ANTHROPIC_FEDERATION_ISSUERS,
    )
    def seed(self, *args) -> None:
        api_session = Mock()
        self._seed_organization(api_session)
        self._seed_users(api_session)
        self._seed_workspaces(api_session)
        self._seed_service_accounts(api_session)
        self._seed_federation(api_session)
        self._seed_apikeys(api_session)

    def _seed_service_accounts(self, api_session: Mock) -> None:
        cartography.intel.anthropic.serviceaccounts.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.anthropic.com/v1",
                "ORG_ID": ORG_ID,
            },
        )

    def _seed_federation(self, api_session: Mock) -> None:
        cartography.intel.anthropic.federation.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.anthropic.com/v1",
                "ORG_ID": ORG_ID,
            },
        )

    def _seed_organization(self, api_session: Mock) -> None:
        cartography.intel.anthropic.organization.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.anthropic.com/v1",
            },
        )

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
