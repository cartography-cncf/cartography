from unittest.mock import patch

import cartography.intel.lastpass.users
import tests.data.lastpass.users
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = 11223344


@patch.object(cartography.intel.lastpass.users, 'get', return_value=tests.data.lastpass.users.LASTPASS_USERS)
def test_load_lastpass_users(mock_api, neo4j_session):
    """
    Ensure that users actually get loaded
    """

    # Arrange
    # LastPass intel only link users to existing Humans (created by other module like Gsuite)
    # We have to create mock humans to tests rels are well created by Lastpass module
    query = """
    UNWIND $UserData as user

    MERGE (h:Human{id: user})
    ON CREATE SET h.firstseen = timestamp()
    SET h.email = user,
    h.email = user,
    h.lastupdated = $UpdateTag
    """
    data = []
    for v in tests.data.lastpass.users.LASTPASS_USERS['Users'].values():
        data.append(v['username'])
    neo4j_session.run(
        query,
        UserData=data,
        UpdateTag=TEST_UPDATE_TAG,
    )

    # Act
    cartography.intel.lastpass.users.sync(
        neo4j_session,
        'fakeProvHash',
        TEST_TENANT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "TENANT_ID": TEST_TENANT_ID},
    )

    # Assert Human exists
    expected_nodes = {
        ('john.doe@domain.tld', 'john.doe@domain.tld'),
        ('jane.smith@domain.tld', 'jane.smith@domain.tld'),
    }
    assert check_nodes(neo4j_session, 'Human', ['id', 'email']) == expected_nodes

    # Assert Tenant exists
    expected_nodes = {
        (TEST_TENANT_ID,),
    }
    assert check_nodes(neo4j_session, 'LastpassTenant', ['id']) == expected_nodes

    # Assert Users exists
    expected_nodes = {
        (123456, 'john.doe@domain.tld'),
        (234567, 'jane.smith@domain.tld'),
    }
    assert check_nodes(neo4j_session, 'LastpassUser', ['id', 'email']) == expected_nodes

    # Assert Users are connected with Tenant
    expected_rels = {
        (123456, TEST_TENANT_ID),
        (234567, TEST_TENANT_ID),
    }
    assert check_rels(
        neo4j_session,
        'LastpassUser', 'id',
        'LastpassTenant', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == expected_rels

    # Assert Users are connected with Humans
    expected_rels = {
        (123456, 'john.doe@domain.tld'),
        (234567, 'jane.smith@domain.tld'),
    }
    assert check_rels(
        neo4j_session,
        'LastpassUser', 'id',
        'Human', 'email',
        'IDENTITY_LASTPASS',
        rel_direction_right=False,
    ) == expected_rels
