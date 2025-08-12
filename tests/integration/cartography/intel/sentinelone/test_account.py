from cartography.intel.sentinelone.account import sync_accounts
from tests.data.sentinelone.account import ACCOUNT_ID
from tests.data.sentinelone.account import ACCOUNT_ID_2
from tests.data.sentinelone.account import ACCOUNTS_DATA
from tests.integration.util import check_nodes

TEST_UPDATE_TAG = 123456789


def test_sync_account(neo4j_session, mocker):
    """
    Ensure that sync_account works properly by syncing only requested accounts
    and returns a list of account IDs.
    """
    mocker.patch(
        "cartography.intel.sentinelone.account.call_sentinelone_api",
        return_value={
            "data": ACCOUNTS_DATA,
        },
    )

    # Create common job parameters required by the new sync function
    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "API_URL": "https://test-api.sentinelone.net",
        "API_TOKEN": "test-api-token",
    }

    account_ids = [ACCOUNT_ID, ACCOUNT_ID_2]
    synced_account_ids = sync_accounts(
        neo4j_session,
        common_job_parameters,
        account_ids,
    )

    # Verify the return value is correct
    assert synced_account_ids == account_ids

    # Verify that only the correct accounts were synced to Neo4j with the right fields
    expected_nodes = {
        (
            ACCOUNT_ID,
            ACCOUNTS_DATA[0]["name"],
            ACCOUNTS_DATA[0]["accountType"],
            ACCOUNTS_DATA[0]["activeAgents"],
            ACCOUNTS_DATA[0]["createdAt"],
            ACCOUNTS_DATA[0]["expiration"],
            ACCOUNTS_DATA[0]["numberOfSites"],
            ACCOUNTS_DATA[0]["state"],
        ),
        (
            ACCOUNT_ID_2,
            ACCOUNTS_DATA[1]["name"],
            ACCOUNTS_DATA[1]["accountType"],
            ACCOUNTS_DATA[1]["activeAgents"],
            ACCOUNTS_DATA[1]["createdAt"],
            ACCOUNTS_DATA[1]["expiration"],
            ACCOUNTS_DATA[1]["numberOfSites"],
            ACCOUNTS_DATA[1]["state"],
        ),
    }

    actual_nodes = check_nodes(
        neo4j_session,
        "S1Account",
        [
            "id",
            "name",
            "account_type",
            "active_agents",
            "created_at",
            "expiration",
            "number_of_sites",
            "state",
        ],
    )

    assert actual_nodes == expected_nodes
