from unittest.mock import Mock

from cartography.intel.duo.api_host import sync_duo_api_host
from cartography.intel.duo.endpoints import sync_duo_endpoints
from cartography.intel.duo.groups import sync_duo_groups
from cartography.intel.duo.phones import sync as sync_duo_phones
from cartography.intel.duo.tokens import sync as sync_duo_tokens
from cartography.intel.duo.users import sync_duo_users
from cartography.intel.duo.web_authn_credentials import sync as sync_duo_web_authn_credentials
from tests.data.duo.endpoints import GET_ENDPOINTS_RESPONSE
from tests.data.duo.groups import GET_GROUPS_RESPONSE
from tests.data.duo.phones import GET_PHONES_RESPONSE
from tests.data.duo.tokens import GET_TOKENS_RESPONSE
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


def test_sync_duo_users(neo4j_session):
    # Arrange
    mock_client = Mock(
        get_users=Mock(return_value=GET_USERS_RESPONSE),
        get_groups=Mock(return_value=GET_GROUPS_RESPONSE),
        get_endpoints=Mock(return_value=GET_ENDPOINTS_RESPONSE),
        get_phones=Mock(return_value=GET_PHONES_RESPONSE),
        get_tokens=Mock(return_value=GET_TOKENS_RESPONSE),
        get_webauthncredentials=Mock(return_value=GET_WEBAUTHNCREDENTIALS_RESPONSE),
    )

    # Act
    sync_duo_api_host(neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_endpoints(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_phones(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_tokens(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_web_authn_credentials(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    sync_duo_groups(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)
    neo4j_session.run(
        'UNWIND $data as item MERGE (h:Human{email: item.email})',
        data=GET_USERS_RESPONSE,
    )
    sync_duo_users(mock_client, neo4j_session, COMMON_JOB_PARAMETERS)

    # Assert
    assert check_nodes(
        neo4j_session,
        'DuoUser',
        ['id', 'user_id', 'username', 'email'],
    ) == {
        ('userid1', 'userid1', 'username1', 'email1@example.com'),
        ('userid2', 'userid2', 'username2', 'email2@example.com'),
        ('userid3', 'userid3', 'username3', 'email3@example.com'),
        ('userid4', 'userid4', 'username4', 'email4@example.com'),
    }

    assert check_rels(
        neo4j_session,
        'DuoApiHost', 'id',
        'DuoUser', 'id',
        'RESOURCE',
        rel_direction_right=True,
    ) == {
        (TEST_API_HOSTNAME, 'userid1'),
        (TEST_API_HOSTNAME, 'userid2'),
        (TEST_API_HOSTNAME, 'userid3'),
        (TEST_API_HOSTNAME, 'userid4'),
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

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoToken', 'id',
        'HAS_DUO_TOKEN',
        rel_direction_right=True,
    ) == {
        ('userid1', 'tokenid1'),
        ('userid1', 'tokenid2'),
        ('userid3', 'tokenid3'),
    }

    assert check_rels(
        neo4j_session,
        'DuoUser', 'id',
        'DuoWebAuthnCredential', 'id',
        'HAS_DUO_WEB_AUTHN_CREDENTIAL',
        rel_direction_right=True,
    ) == {
        ('userid1', 'webauthnkey1'),
        ('userid1', 'webauthnkey2'),
        ('userid2', 'webauthnkey3'),
    }

    assert check_rels(
        neo4j_session,
        'DuoGroup', 'id',
        'DuoUser', 'id',
        'MEMBER_OF_DUO_GROUP',
        rel_direction_right=False,
    ) == {
        ('groupid1', 'userid1'),
        ('groupid2', 'userid1'),
        ('groupid2', 'userid2'),
        ('groupid3', 'userid3'),
        ('groupid4', 'userid4'),
    }

    assert check_rels(
        neo4j_session,
        'Human', 'email',
        'DuoUser', 'email',
        'IDENTITY_DUO',
        rel_direction_right=True,
    ) == {
        ('email1@example.com', 'email1@example.com'),
        ('email2@example.com', 'email2@example.com'),
        ('email3@example.com', 'email3@example.com'),
        ('email4@example.com', 'email4@example.com'),
    }
