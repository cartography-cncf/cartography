from cartography.client.core.tx import load
from cartography.intel.github.users import load_users
from cartography.models.github.users import GitHubOrganizationUserSchema
from tests.data.graph.querybuilder.sample_data.case_insensitive_prop_ref import FAKE_EMPLOYEE2_DATA
from tests.data.graph.querybuilder.sample_data.case_insensitive_prop_ref import FAKE_GITHUB_ORG_DATA
from tests.data.graph.querybuilder.sample_data.case_insensitive_prop_ref import FAKE_GITHUB_USER_DATA
from tests.data.graph.querybuilder.sample_models.fake_emps_githubusers_fuzzy import FakeEmp2Schema
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


def test_load_team_members_data_fuzzy(neo4j_session):
    # Arrange: Load some fake GitHubUser nodes to the graph
    load_users(
        neo4j_session,
        GitHubOrganizationUserSchema(),
        FAKE_GITHUB_USER_DATA,
        FAKE_GITHUB_ORG_DATA,
        TEST_UPDATE_TAG,
    )

    # Act: Create team members
    load(neo4j_session, FakeEmp2Schema(), FAKE_EMPLOYEE2_DATA, lastupdated=TEST_UPDATE_TAG)

    # Assert we can create relationships using a fuzzy, case insensitive match
    assert check_rels(neo4j_session, 'FakeEmployee2', 'email', 'GitHubUser', 'username', 'IDENTITY_GITHUB') == {
        ('hjsimpson@example.com', 'HjsimPson'), ('mbsimpson@example.com', 'mbsimp-son'),
    }
