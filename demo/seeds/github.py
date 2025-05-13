import neo4j
from unittest.mock import patch
from unittest import TestCase

import cartography.intel.github.users
import cartography.intel.github.repos
import cartography.intel.github.teams
import tests.data.github.repos
import tests.data.github.teams
import tests.data.github.users

TEST_GITHUB_URL = tests.data.github.users.GITHUB_ORG_DATA["url"]
TEST_GITHUB_ORG = tests.data.github.users.GITHUB_ORG_DATA["login"]
FAKE_API_KEY = "asdf"


class GithubSeed(TestCase):
    def __init__(self, neo4j_session: neo4j.Session, update_tag: int):
        super().__init__("seed")
        self.neo4j_session = neo4j_session
        self.update_tag = update_tag

    @patch.object(
        cartography.intel.github.users,
        "get_users",
        return_value=tests.data.github.users.GITHUB_USER_DATA,
    )
    @patch.object(
        cartography.intel.github.users,
        "get_enterprise_owners",
        return_value=tests.data.github.users.GITHUB_ENTERPRISE_OWNER_DATA,
    )
    @patch.object(
        cartography.intel.github.teams,
        "_get_child_teams",
        return_value=tests.data.github.teams.GH_TEAM_CHILD_TEAM,
    )
    @patch.object(
        cartography.intel.github.teams,
        "_get_team_users",
        return_value=tests.data.github.teams.GH_TEAM_USERS,
    )
    @patch.object(
        cartography.intel.github.teams,
        "_get_team_repos",
        return_value=tests.data.github.teams.GH_TEAM_REPOS,
    )
    @patch.object(cartography.intel.github.teams, "get_teams", return_value=tests.data.github.teams.GH_TEAM_DATA)
    def seed(self, 
        mock_teams,
        mock_team_repos,
        mock_team_users,
        mock_team_child,
        mock_owners,
        mock_users
        ) -> None:
        # DOC
        self._seed_users()
        self._seed_repos()
        self._seed_teams()

    def _seed_users(self) -> None:
        cartography.intel.github.users.sync(
            self.neo4j_session,
            {"UPDATE_TAG": self.update_tag},
            FAKE_API_KEY,
            TEST_GITHUB_URL,
            TEST_GITHUB_ORG,
        )

    def _seed_repos(self) -> None:
        repos_data = cartography.intel.github.repos.transform(
            tests.data.github.repos.GET_REPOS,
            tests.data.github.repos.DIRECT_COLLABORATORS,
            tests.data.github.repos.OUTSIDE_COLLABORATORS,
        )
        cartography.intel.github.repos.load_github_repos(
            self.neo4j_session,
            self.update_tag,
            repos_data["repos"],
        )
        cartography.intel.github.repos.load_github_owners(
            self.neo4j_session,
            self.update_tag,
            repos_data["repo_owners"],
        )
        cartography.intel.github.repos.load_github_languages(
            self.neo4j_session,
            self.update_tag,
            repos_data["repo_languages"],
        )

    def _seed_teams(self) -> None:
        cartography.intel.github.teams.sync_github_teams(
            self.neo4j_session,
            {"UPDATE_TAG": self.update_tag},
            FAKE_API_KEY,
            TEST_GITHUB_URL,
            "example_org",
        )
