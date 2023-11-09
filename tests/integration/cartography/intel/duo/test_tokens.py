from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.tokens import sync as sync_duo_tokens
from cartography.intel.duo.users import sync_duo_users
from tests.data.duo.tokens import GET_TOKENS_RESPONSE
from tests.data.duo.users import GET_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_tokens(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_users=Mock(return_value=GET_USERS_RESPONSE),
        get_tokens=Mock(return_value=GET_TOKENS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_tokens(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoToken',
        ['id', 'token_id', 'serial', 'type'],
    ) == {
        ('tokenid1', 'tokenid1', 'serial1', 'yk'),
        ('tokenid2', 'tokenid2', 'serial2', 'yk'),
        ('tokenid3', 'tokenid3', 'serial3', 'yk'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoToken', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'tokenid1'),
        (TEST_API_HOSTNAME, 'tokenid2'),
        (TEST_API_HOSTNAME, 'tokenid3'),
    }

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoToken', 'id',
        'HAS_DUO_TOKEN',
        rel_direction_right=True,
    ) == {
        ('userid1', 'tokenid1'),
        ('userid3', 'tokenid3'),
    }
