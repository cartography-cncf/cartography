from typing import Any

import cartography.intel.airbyte.connections
import cartography.intel.airbyte.destinations
import cartography.intel.airbyte.organizations
import cartography.intel.airbyte.sources
import cartography.intel.airbyte.tags
import cartography.intel.airbyte.users
import cartography.intel.airbyte.workspaces
import tests.data.airbyte.connections
import tests.data.airbyte.destinations
import tests.data.airbyte.organizations
import tests.data.airbyte.sources
import tests.data.airbyte.tags
import tests.data.airbyte.users
import tests.data.airbyte.workspaces
from demo.seeds.base import Seed

ORG_ID = "31634962-4b3c-4b0c-810d-a2a77d6df222"


class AirbyteSeed(Seed):

    def seed(self, *args) -> None:
        self._seed_organization()
        self._seed_workspaces()
        self._seed_users()
        self._seed_tags()
        self._seed_sources()
        self._seed_destinations()
        self._seed_connections()

    def _seed_organization(self) -> None:
        cartography.intel.airbyte.organizations.load_organizations(
            self.neo4j_session,
            tests.data.airbyte.organizations.AIRBYTE_ORGANIZATIONS,
            self.update_tag,
        )

    def _seed_workspaces(self) -> None:
        cartography.intel.airbyte.workspaces.load_workspaces(
            self.neo4j_session,
            tests.data.airbyte.workspaces.AIRBYTE_WORKSPACES,
            ORG_ID,
            self.update_tag,
        )

    def _seed_users(self) -> None:
        users: list[dict[str, Any]] = []
        for u in tests.data.airbyte.users.AIRBYTE_USERS:
            user: dict[str, Any] = u.copy()
            permissions = []
            for permission in tests.data.airbyte.users.AIRBYTE_USERS_PERMISSIONS:
                if permission["userId"] == user["id"]:
                    permissions.append(permission)
            org_admin, workspace_admin, workspace_member = (
                cartography.intel.airbyte.users.transform_permissions(permissions)
            )
            user["adminOfOrganization"] = org_admin
            user["adminOfWorkspace"] = workspace_admin
            user["memberOfWorkspace"] = workspace_member
            users.append(user)
        cartography.intel.airbyte.users.load_users(
            self.neo4j_session, users, org_id=ORG_ID, update_tag=self.update_tag
        )

    def _seed_tags(self) -> None:
        cartography.intel.airbyte.tags.load_tags(
            self.neo4j_session,
            tests.data.airbyte.tags.AIRBYTE_TAGS,
            ORG_ID,
            self.update_tag,
        )

    def _seed_sources(self) -> None:
        cartography.intel.airbyte.sources.load_sources(
            self.neo4j_session,
            tests.data.airbyte.sources.AIRBYTE_SOURCES,
            ORG_ID,
            self.update_tag,
        )

    def _seed_destinations(self) -> None:
        cartography.intel.airbyte.destinations.load_destinations(
            self.neo4j_session,
            tests.data.airbyte.destinations.AIRBYTE_DESTINATIONS,
            ORG_ID,
            self.update_tag,
        )

    def _seed_connections(self) -> None:
        connections, streams = cartography.intel.airbyte.connections.transform(
            tests.data.airbyte.connections.AIRBYTE_CONNECTIONS
        )
        cartography.intel.airbyte.connections.load_connections(
            self.neo4j_session, connections, ORG_ID, self.update_tag
        )
        cartography.intel.airbyte.connections.load_streams(
            self.neo4j_session, streams, ORG_ID, self.update_tag
        )
