from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.endpoints import sync_duo_endpoints
from cartography.intel.duo.users import sync_duo_users
from tests.data.duo.endpoints import GET_ENDPOINTS_RESPONSE
from tests.data.duo.users import GET_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_endpoints(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_users=Mock(return_value=GET_USERS_RESPONSE),
        get_endpoints=Mock(return_value=GET_ENDPOINTS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_endpoints(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoEndpoint',
        ['id', 'epkey', 'os_family', 'email', 'username'],
    ) == {
        ('epkey1', 'epkey1', 'iOS', 'email1@example.com', 'username1'),
        ('epkey2', 'epkey2', 'iOS', 'email2@example.com', 'username2'),
        ('epkey3', 'epkey3', 'iOS', 'email3@example.com', 'username3'),
        ('epkey4', 'epkey4', 'iOS', 'email4@example.com', 'username4'),
        ('epkey5', 'epkey5', 'iOS', 'email5@example.com', 'username5'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoEndpoint', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'epkey1'),
        (TEST_API_HOSTNAME, 'epkey2'),
        (TEST_API_HOSTNAME, 'epkey3'),
        (TEST_API_HOSTNAME, 'epkey4'),
        (TEST_API_HOSTNAME, 'epkey5'),
    }

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoEndpoint', 'id',
        'HAS_DUO_ENDPOINT',
        rel_direction_right=True,
    ) == {
        ('userid1', 'epkey1'),
        ('userid2', 'epkey2'),
        ('userid3', 'epkey3'),
        ('userid4', 'epkey4'),
    }
