from copy import deepcopy
from unittest.mock import Mock
from unittest.mock import patch

import requests

import cartography.intel.salesforce.connectedapps
import cartography.intel.salesforce.users
import tests.data.salesforce.data as test_data
from tests.integration.cartography.intel.salesforce.test_organization import (
    _ensure_local_neo4j_has_test_organization,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789


@patch.object(
    cartography.intel.salesforce.connectedapps,
    "get_oauth_tokens",
    return_value=deepcopy(test_data.SALESFORCE_OAUTH_TOKENS),
)
@patch.object(
    cartography.intel.salesforce.connectedapps,
    "get_apps",
    return_value=deepcopy(test_data.SALESFORCE_CONNECTED_APPS),
)
def test_sync_salesforce_connected_apps(mock_apps, mock_tokens, neo4j_session):
    # Arrange
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    cartography.intel.salesforce.users.load_users(
        neo4j_session, test_data.SALESFORCE_USERS, test_data.ORG_ID, TEST_UPDATE_TAG
    )
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID}

    # Act
    cartography.intel.salesforce.connectedapps.sync(
        neo4j_session, Mock(), common_job_parameters
    )

    # Assert nodes (also carry the ThirdPartyApp label)
    assert check_nodes(neo4j_session, "SalesforceConnectedApp", ["id", "name"]) == {
        ("0Ci000000000001AAA", "Slack"),
    }
    assert check_nodes(neo4j_session, "ThirdPartyApp", ["id"]) == {
        ("0Ci000000000001AAA",),
    }

    # Assert authorization edge derived from OAuthToken (joined by app name)
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceConnectedApp",
        "id",
        "AUTHORIZED",
        rel_direction_right=True,
    ) == {
        ("005000000000001AAA", "0Ci000000000001AAA"),
    }


@patch.object(cartography.intel.salesforce.connectedapps, "get_oauth_tokens")
@patch.object(cartography.intel.salesforce.connectedapps, "get_apps")
def test_oauth_token_access_error_preserves_previous_connected_app_snapshot(
    mock_apps, mock_tokens, neo4j_session
):
    # Arrange
    _ensure_local_neo4j_has_test_organization(neo4j_session)
    cartography.intel.salesforce.users.load_users(
        neo4j_session, test_data.SALESFORCE_USERS, test_data.ORG_ID, TEST_UPDATE_TAG
    )
    response = Mock()
    response.json.return_value = [
        {
            "message": "sObject type 'OAuthToken' is not supported.",
            "errorCode": "INVALID_TYPE",
        }
    ]
    mock_apps.side_effect = [
        deepcopy(test_data.SALESFORCE_CONNECTED_APPS),
        deepcopy(test_data.SALESFORCE_CONNECTED_APPS),
    ]
    mock_tokens.side_effect = [
        deepcopy(test_data.SALESFORCE_OAUTH_TOKENS),
        requests.HTTPError(response=response),
    ]
    cartography.intel.salesforce.connectedapps.sync(
        neo4j_session,
        Mock(),
        {"UPDATE_TAG": TEST_UPDATE_TAG, "ORG_ID": test_data.ORG_ID},
    )

    # Act
    cartography.intel.salesforce.connectedapps.sync(
        neo4j_session,
        Mock(),
        {"UPDATE_TAG": TEST_UPDATE_TAG + 1, "ORG_ID": test_data.ORG_ID},
    )

    # Assert
    assert check_nodes(
        neo4j_session, "SalesforceConnectedApp", ["id", "lastupdated"]
    ) == {("0Ci000000000001AAA", TEST_UPDATE_TAG)}
    assert check_rels(
        neo4j_session,
        "SalesforceUser",
        "id",
        "SalesforceConnectedApp",
        "id",
        "AUTHORIZED",
        rel_direction_right=True,
    ) == {("005000000000001AAA", "0Ci000000000001AAA")}
