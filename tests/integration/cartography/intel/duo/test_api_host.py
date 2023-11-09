from cartography.intel.duo.api_host import sync_duo_api_host
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_api_host(neo4j_session):
    # Arrange, Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(neo4j_session, 'DuoApiHost', ['id']) == {
        (TEST_API_HOSTNAME,),
    }
