from unittest.mock import patch

import cartography.intel.bigfix.computers
from cartography.intel.bigfix.computers import sync
from tests.data.bigfix.computers import BF_COMPUTER_DETAILS
from tests.data.bigfix.computers import BF_COMPUTER_LIST
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_TENANT_ID = 11223344


@patch.object(cartography.intel.bigfix.computers, '_get_computer_details_raw_xml', side_effect=BF_COMPUTER_DETAILS)
@patch.object(cartography.intel.bigfix.computers, '_get_computer_list_raw_xml', return_value=BF_COMPUTER_LIST)
def test_sync(mock_list, mock_details, neo4j_session):
    # Act
    bigfix_root_url = 'https://bigfixroot.example.com'
    sync(
        neo4j_session,
        bigfix_root_url,
        'myuser',
        'mypassword',
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ROOT_URL": bigfix_root_url},
    )

    # Assert
    assert check_nodes(neo4j_session, 'BigfixComputer', ['id', 'dnsname', 'devicetype', 'islocked']) == {
        ('223212', 'my-server-2.example.com', 'Server', False),
        ('302143', 'WIN-AFAFAF.example.com', 'Laptop', False),
        ('540385', 'WIN-ABCD.example.com', 'Laptop', False),
    }

    assert check_rels(
        neo4j_session,
        'BigfixComputer', 'id',
        'BigfixRoot', 'id',
        'RESOURCE',
        rel_direction_right=False,
    ) == {
        ('223212', bigfix_root_url),
        ('302143', bigfix_root_url),
        ('540385', bigfix_root_url),
    }
