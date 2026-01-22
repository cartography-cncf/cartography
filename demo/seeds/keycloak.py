from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.keycloak.authenticationexecutions
import cartography.intel.keycloak.authenticationflows
import cartography.intel.keycloak.clients
import cartography.intel.keycloak.groups
import cartography.intel.keycloak.identityproviders
import cartography.intel.keycloak.organizations
import cartography.intel.keycloak.realms
import cartography.intel.keycloak.roles
import cartography.intel.keycloak.scopes
import cartography.intel.keycloak.users
import tests.data.keycloak.authenticationexecutions
import tests.data.keycloak.authenticationflows
import tests.data.keycloak.clients
import tests.data.keycloak.groups
import tests.data.keycloak.identityproviders
import tests.data.keycloak.organizations
import tests.data.keycloak.realms
import tests.data.keycloak.roles
import tests.data.keycloak.scopes
import tests.data.keycloak.users
from demo.seeds.base import Seed

BASE_URL = "https://keycloak.example.com"


class KeycloakSeed(Seed):
    @patch.object(
        cartography.intel.keycloak.realms,
        "get",
        return_value=tests.data.keycloak.realms.KEYCLOAK_REALMS,
    )
    @patch.object(
        cartography.intel.keycloak.users,
        "get",
        return_value=tests.data.keycloak.users.KEYCLOAK_USERS,
    )
    @patch.object(
        cartography.intel.keycloak.groups,
        "get",
        return_value=tests.data.keycloak.groups.KEYCLOAK_GROUPS,
    )
    @patch.object(
        cartography.intel.keycloak.roles,
        "get",
        return_value=tests.data.keycloak.roles.KEYCLOAK_ROLES,
    )
    @patch.object(
        cartography.intel.keycloak.roles,
        "get_mapping",
        return_value=tests.data.keycloak.roles.KEYCLOAK_ROLES_MAPPING,
    )
    @patch.object(
        cartography.intel.keycloak.clients,
        "get",
        return_value=tests.data.keycloak.clients.KEYCLOAK_CLIENTS,
    )
    @patch.object(
        cartography.intel.keycloak.scopes,
        "get",
        return_value=tests.data.keycloak.scopes.KEYCLOAK_SCOPES,
    )
    @patch.object(
        cartography.intel.keycloak.identityproviders,
        "get",
        return_value=tests.data.keycloak.identityproviders.KEYCLOAK_IDPS,
    )
    @patch.object(
        cartography.intel.keycloak.authenticationflows,
        "get",
        return_value=tests.data.keycloak.authenticationflows.KEYCLOAK_AUTHENTICATIONFLOWS,
    )
    @patch.object(
        cartography.intel.keycloak.authenticationexecutions,
        "get",
        return_value=tests.data.keycloak.authenticationexecutions.KEYCLOAK_AUTHENTICATIONEXECUTIONS,
    )
    @patch.object(
        cartography.intel.keycloak.organizations,
        "get",
        return_value=tests.data.keycloak.organizations.KEYCLOAK_ORGANIZATIONS,
    )
    def seed(self, *args) -> None:
        api_session = Mock()
        realms = self._seed_realms(api_session)
        for realm in realms:
            realm_name = realm["realm"]
            realm_id = realm["id"]
            self._seed_users(api_session, realm_name)
            self._seed_identity_providers(api_session, realm_name)
            scopes = self._seed_scopes(api_session, realm_name)
            scope_ids = [scope["id"] for scope in scopes]
            auth_flows = self._seed_authentication_flows(api_session, realm_name)
            flow_aliases = {flow["alias"]: flow["id"] for flow in auth_flows}
            realm_default_flows = {
                "browser": flow_aliases.get(realm.get("browserFlow")),
                "registration": flow_aliases.get(realm.get("registrationFlow")),
                "direct_grant": flow_aliases.get(realm.get("directGrantFlow")),
                "reset_credentials": flow_aliases.get(
                    realm.get("resetCredentialsFlow")
                ),
                "client_authentication": flow_aliases.get(
                    realm.get("clientAuthenticationFlow")
                ),
                "docker_authentication": flow_aliases.get(
                    realm.get("dockerAuthenticationFlow")
                ),
                "first_broker_login": flow_aliases.get(
                    realm.get("firstBrokerLoginFlow")
                ),
            }
            self._seed_authentication_executions(
                api_session, realm_name, realm_id, list(flow_aliases.keys())
            )
            clients = self._seed_clients(
                api_session, realm_name, realm_id, realm_default_flows
            )
            client_ids = [client["id"] for client in clients]
            self._seed_roles(api_session, realm_name, client_ids, scope_ids)
            self._seed_groups(api_session, realm_name)
            self._seed_organizations(api_session, realm_name)

    def _seed_realms(self, api_session: Mock) -> list[dict]:
        return cartography.intel.keycloak.realms.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
            },
        )

    def _seed_users(self, api_session: Mock, realm_name: str) -> None:
        cartography.intel.keycloak.users.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
        )

    def _seed_groups(self, api_session: Mock, realm_name: str) -> None:
        cartography.intel.keycloak.groups.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
        )

    def _seed_roles(
        self,
        api_session: Mock,
        realm_name: str,
        client_ids: list[str],
        scope_ids: list[str],
    ) -> None:
        cartography.intel.keycloak.roles.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
            client_ids=client_ids,
            scope_ids=scope_ids,
        )

    def _seed_clients(
        self,
        api_session: Mock,
        realm_name: str,
        realm_id: str,
        realm_default_flows: dict[str, Any],
    ) -> list[dict]:
        # Default flows for the realm
        return cartography.intel.keycloak.clients.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
                "REALM_ID": realm_id,
            },
            realm_default_flows=realm_default_flows,
        )

    def _seed_scopes(self, api_session: Mock, realm_name: str) -> list[dict]:
        return cartography.intel.keycloak.scopes.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
        )

    def _seed_identity_providers(self, api_session: Mock, realm_name: str) -> None:
        cartography.intel.keycloak.identityproviders.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
        )

    def _seed_authentication_flows(
        self, api_session: Mock, realm_name: str
    ) -> list[dict]:
        return cartography.intel.keycloak.authenticationflows.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
        )

    def _seed_authentication_executions(
        self, api_session: Mock, realm_name: str, realm_id: str, flow_aliases: list[str]
    ) -> None:
        cartography.intel.keycloak.authenticationexecutions.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
                "REALM_ID": realm_id,
            },
            flow_aliases=flow_aliases,
        )

    def _seed_organizations(self, api_session: Mock, realm_name: str) -> None:
        cartography.intel.keycloak.organizations.sync(
            self.neo4j_session,
            api_session,
            base_url=BASE_URL,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "REALM": realm_name,
            },
        )
