from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.groups import sync_duo_groups
from tests.data.duo.groups import GET_GROUPS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_groups(neo4j_session):
    # Arrange
    mock_client = Mock(get_groups=Mock(return_value=GET_GROUPS_RESPONSE))

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_groups(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoGroup',
        ['id', 'group_id', 'name', 'desc'],
    ) == {
        ('groupid1', 'groupid1', 'name1', 'desc1'),
        ('groupid2', 'groupid2', 'name2', 'desc2'),
        ('groupid3', 'groupid3', 'name3', 'desc3'),
        ('groupid4', 'groupid4', 'name4', 'desc4'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoGroup', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'groupid1'),
        (TEST_API_HOSTNAME, 'groupid2'),
        (TEST_API_HOSTNAME, 'groupid3'),
        (TEST_API_HOSTNAME, 'groupid4'),
    }
