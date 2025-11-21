from unittest.mock import Mock

import cartography.intel.duo.api_host
import cartography.intel.duo.endpoints
import cartography.intel.duo.groups
import cartography.intel.duo.phones
import cartography.intel.duo.tokens
import cartography.intel.duo.users
import cartography.intel.duo.web_authn_credentials
import tests.data.duo.endpoints
import tests.data.duo.groups
import tests.data.duo.phones
import tests.data.duo.tokens
import tests.data.duo.users
import tests.data.duo.web_authn_credentials
from demo.seeds.base import Seed

API_HOSTNAME = "https://api-1234.duo.com"


class DuoSeed(Seed):
    @property
    def common_job_parameters(self) -> dict:
        return {
            "DUO_API_HOSTNAME": API_HOSTNAME,
            "UPDATE_TAG": self.update_tag,
        }

    def seed(self, *args) -> None:
        mock_client = Mock(
            get_users=Mock(return_value=tests.data.duo.users.GET_USERS_RESPONSE),
            get_tokens=Mock(return_value=tests.data.duo.tokens.GET_TOKENS_RESPONSE),
            get_webauthncredentials=Mock(
                return_value=tests.data.duo.web_authn_credentials.GET_WEBAUTHNCREDENTIALS_RESPONSE
            ),
            get_endpoints=Mock(
                return_value=tests.data.duo.endpoints.GET_ENDPOINTS_RESPONSE
            ),
            get_phones=Mock(return_value=tests.data.duo.phones.GET_PHONES_RESPONSE),
            get_groups=Mock(return_value=tests.data.duo.groups.GET_GROUPS_RESPONSE),
        )

        self._seed_hosts()
        self._seed_tokens(mock_client)
        self._seed_web_authn_credentials(mock_client)
        self._seed_endpoints(mock_client)
        self._seed_phones(mock_client)
        self._seed_groups(mock_client)
        self._seed_users(mock_client)

    def _seed_hosts(self) -> None:
        cartography.intel.duo.api_host.sync_duo_api_host(
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_users(self, mock_client: Mock) -> None:
        cartography.intel.duo.users.sync_duo_users(
            mock_client,
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_tokens(self, mock_client: Mock) -> None:
        cartography.intel.duo.tokens.sync(
            mock_client,
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_web_authn_credentials(self, mock_client: Mock) -> None:
        cartography.intel.duo.web_authn_credentials.sync(
            mock_client,
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_endpoints(self, mock_client: Mock) -> None:
        cartography.intel.duo.endpoints.sync_duo_endpoints(
            mock_client,
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_phones(self, mock_client: Mock) -> None:
        cartography.intel.duo.phones.sync(
            mock_client,
            self.neo4j_session,
            self.common_job_parameters,
        )

    def _seed_groups(self, mock_client: Mock) -> None:
        cartography.intel.duo.groups.sync_duo_groups(
            mock_client,
            self.neo4j_session,
            self.common_job_parameters,
        )
