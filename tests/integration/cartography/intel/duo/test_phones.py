from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.phones import sync as sync_duo_phones
from cartography.intel.duo.users import sync_duo_users
from tests.data.duo.phones import GET_PHONES_RESPONSE
from tests.data.duo.users import GET_USERS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_phones(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_phones=Mock(return_value=GET_PHONES_RESPONSE),
        get_users=Mock(return_value=GET_USERS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_phones(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoPhone',
        ['id', 'phone_id', 'platform'],
    ) == {
        ('phoneid1', 'phoneid1', 'Apple iOS'),
        ('phoneid2', 'phoneid2', 'Apple iOS'),
        ('phoneid3', 'phoneid3', 'Apple iOS'),
        ('phoneid4', 'phoneid4', 'Apple iOS'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoPhone', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'phoneid1'),
        (TEST_API_HOSTNAME, 'phoneid2'),
        (TEST_API_HOSTNAME, 'phoneid3'),
        (TEST_API_HOSTNAME, 'phoneid4'),
    }

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoPhone', 'id',
        'HAS_DUO_PHONE',
        rel_direction_right=True,
    ) == {
        ('userid1', 'phoneid1'),
        ('userid2', 'phoneid2'),
        ('userid3', 'phoneid3'),
        ('userid4', 'phoneid4'),
    }
