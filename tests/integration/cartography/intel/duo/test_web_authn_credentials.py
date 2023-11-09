from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.users import sync_duo_users
from cartography.intel.duo.web_authn_credentials import sync as sync_duo_web_authn_credentials
from tests.data.duo.users import GET_USERS_RESPONSE
from tests.data.duo.web_authn_credentials import GET_WEBAUTHNCREDENTIALS_RESPONSE
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_API_HOSTNAME = 'https://api-1234.duo.com'
COMMON_JOB_PARAMETERS = {
    'DUO_API_HOSTNAME': TEST_API_HOSTNAME,
    'UPDATE_TAG': TEST_UPDATE_TAG,
}


def test_sync_duo_web_authn_credentials(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_users=Mock(return_value=GET_USERS_RESPONSE),
        get_webauthncredentials=Mock(return_value=GET_WEBAUTHNCREDENTIALS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_web_authn_credentials(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoWebAuthnCredential',
        ['id', 'webauthnkey', 'credential_name'],
    ) == {
        ('webauthnkey1', 'webauthnkey1', 'YubiKey'),
        ('webauthnkey2', 'webauthnkey2', 'YubiKey'),
        ('webauthnkey3', 'webauthnkey3', 'YubiKey'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoWebAuthnCredential', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'webauthnkey1'),
        (TEST_API_HOSTNAME, 'webauthnkey2'),
        (TEST_API_HOSTNAME, 'webauthnkey3'),
    }

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoWebAuthnCredential', 'id',
        'HAS_DUO_WEB_AUTHN_CREDENTIAL',
        rel_direction_right=True,
    ) == {
        ('userid1', 'webauthnkey1'),
        ('userid2', 'webauthnkey2'),
        ('userid3', 'webauthnkey3'),
    }
