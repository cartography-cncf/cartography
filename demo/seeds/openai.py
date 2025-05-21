from unittest.mock import Mock
from unittest.mock import patch

import cartography.intel.openai.adminapikeys
import cartography.intel.openai.apikeys
import cartography.intel.openai.projects
import cartography.intel.openai.serviceaccounts
import cartography.intel.openai.users
import tests.data.openai.adminapikeys
import tests.data.openai.apikeys
import tests.data.openai.projects
import tests.data.openai.serviceaccounts
import tests.data.openai.users
from demo.seeds.base import Seed

ORG_ID = "org-iwai3meew4phaeNgu8ae"


class OpenAISeed(Seed):
    @patch.object(
        cartography.intel.openai.projects,
        "get_project_users",
        return_value=tests.data.openai.projects.OPENAI_PROJECTS_MEMBERS,
    )
    @patch.object(
        cartography.intel.openai.projects,
        "get",
        return_value=tests.data.openai.projects.OPENAI_PROJECTS,
    )
    @patch.object(
        cartography.intel.openai.users,
        "get",
        return_value=tests.data.openai.users.OPENAI_USERS,
    )
    @patch.object(
        cartography.intel.openai.apikeys,
        "get",
        return_value=tests.data.openai.apikeys.OPENAI_APIKEYS,
    )
    @patch.object(
        cartography.intel.openai.serviceaccounts,
        "get",
        return_value=tests.data.openai.serviceaccounts.OPENAI_SERVICEACCOUNTS,
    )
    @patch.object(
        cartography.intel.openai.adminapikeys,
        "get",
        return_value=tests.data.openai.adminapikeys.OPENAI_ADMINAPIKEYS,
    )
    def seed(self, *args) -> None:
        api_session = Mock()
        self._seed_users(api_session)
        for project in self._seed_projects(api_session):
            self._seed_serviceaccounts(api_session, project["id"])
            self._seed_apikeys(api_session, project["id"])
        self._seed_admin_apikeys(api_session)

    def _seed_users(self, api_session: Mock) -> None:
        cartography.intel.openai.users.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.openai.com/v1",
                "ORG_ID": ORG_ID,
            },
            ORG_ID=ORG_ID,
        )

    def _seed_projects(self, api_session: Mock) -> list[dict]:
        return cartography.intel.openai.projects.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.openai.com/v1",
                "ORG_ID": ORG_ID,
            },
            ORG_ID=ORG_ID,
        )

    def _seed_serviceaccounts(self, api_session: Mock, project_id: str) -> None:
        cartography.intel.openai.serviceaccounts.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.openai.com/v1",
                "project_id": project_id,
            },
            project_id=project_id,
        )

    def _seed_apikeys(self, api_session: Mock, project_id: str) -> None:
        cartography.intel.openai.apikeys.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.openai.com/v1",
                "project_id": project_id,
            },
            project_id=project_id,
        )

    def _seed_admin_apikeys(self, api_session: Mock) -> None:
        cartography.intel.openai.adminapikeys.sync(
            self.neo4j_session,
            api_session,
            common_job_parameters={
                "UPDATE_TAG": self.update_tag,
                "BASE_URL": "https://api.openai.com/v1",
                "ORG_ID": ORG_ID,
            },
            ORG_ID=ORG_ID,
        )
