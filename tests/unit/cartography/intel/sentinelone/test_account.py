from unittest.mock import MagicMock

import pytest

from cartography.intel.sentinelone.account import get_accounts
from cartography.intel.sentinelone.account import get_sites
from cartography.intel.sentinelone.account import sync_site_scoped_accounts
from cartography.intel.sentinelone.account import transform_accounts
from cartography.intel.sentinelone.account import transform_accounts_from_sites
from tests.data.sentinelone.account import ACCOUNT_ID
from tests.data.sentinelone.account import ACCOUNT_ID_2
from tests.data.sentinelone.account import ACCOUNTS_DATA
from tests.data.sentinelone.account import SITES_DATA


def test_transform_accounts():
    """
    Test that transform_accounts correctly transforms raw API data
    """
    result = transform_accounts(ACCOUNTS_DATA)

    assert len(result) == 3

    # Test first account
    account1 = result[0]
    assert account1["id"] == ACCOUNTS_DATA[0]["id"]
    assert account1["name"] == ACCOUNTS_DATA[0]["name"]
    assert account1["account_type"] == ACCOUNTS_DATA[0]["accountType"]
    assert account1["active_agents"] == ACCOUNTS_DATA[0]["activeAgents"]
    assert account1["created_at"] == ACCOUNTS_DATA[0]["createdAt"]
    assert account1["expiration"] == ACCOUNTS_DATA[0]["expiration"]
    assert account1["number_of_sites"] == ACCOUNTS_DATA[0]["numberOfSites"]
    assert account1["state"] == ACCOUNTS_DATA[0]["state"]

    # Test second account
    account2 = result[1]
    assert account2["id"] == ACCOUNTS_DATA[1]["id"]
    assert account2["name"] == ACCOUNTS_DATA[1]["name"]
    assert account2["account_type"] == ACCOUNTS_DATA[1]["accountType"]


def test_transform_accounts_missing_optional_fields():
    """
    Test that transform_accounts handles missing optional fields gracefully
    """
    test_data = [
        {
            "id": "required-id",
            # Missing all optional fields
        }
    ]

    result = transform_accounts(test_data)

    assert len(result) == 1
    account = result[0]

    # Required field should be present
    assert account["id"] == "required-id"

    # Optional fields should be None
    assert account["name"] is None
    assert account["account_type"] is None
    assert account["active_agents"] is None
    assert account["created_at"] is None
    assert account["expiration"] is None
    assert account["number_of_sites"] is None
    assert account["state"] is None


def test_transform_accounts_empty_list():
    """
    Test that transform_accounts handles empty input list
    """
    result = transform_accounts([])
    assert result == []


def test_transform_accounts_from_sites_groups_parent_accounts():
    result = transform_accounts_from_sites(SITES_DATA)

    assert result == [
        {
            "id": ACCOUNT_ID,
            "name": "Test Account",
            "account_type": None,
            "active_agents": 5,
            "created_at": "2023-01-01T00:00:00Z",
            "expiration": "2025-01-01T00:00:00Z",
            "number_of_sites": 2,
            "state": "active",
        },
        {
            "id": ACCOUNT_ID_2,
            "name": "Test Account 2",
            "account_type": None,
            "active_agents": 1,
            "created_at": "2023-01-02T00:00:00Z",
            "expiration": "2025-01-02T00:00:00Z",
            "number_of_sites": 1,
            "state": "active",
        },
    ]


def test_transform_accounts_from_sites_raises_for_missing_account_id():
    with pytest.raises(KeyError):
        transform_accounts_from_sites(
            [
                {
                    "id": "site-1",
                    "accountName": "Test Account",
                },
            ]
        )


def test_sync_site_scoped_accounts_raises_for_missing_site_id(mocker):
    mocker.patch(
        "cartography.intel.sentinelone.account.get_sites",
        return_value=[
            {
                "accountId": ACCOUNT_ID,
                "accountName": "Test Account",
            },
        ],
    )
    mocker.patch("cartography.intel.sentinelone.account.load_accounts")

    with pytest.raises(KeyError):
        sync_site_scoped_accounts(
            MagicMock(),
            {
                "API_URL": "https://test-api.sentinelone.net",
                "API_TOKEN": "test-api-token",
                "UPDATE_TAG": 123,
            },
        )


def test_get_sites_paginates(mocker):
    mock_call = mocker.patch(
        "cartography.intel.sentinelone.account.call_sentinelone_api",
        side_effect=[
            {
                "data": {"sites": [SITES_DATA[0]]},
                "pagination": {"nextCursor": "cursor-1"},
            },
            {
                "data": {"sites": [SITES_DATA[1], SITES_DATA[2]]},
                "pagination": {},
            },
        ],
    )

    result = get_sites("https://test-api.sentinelone.net", "test-api-token")

    assert result == SITES_DATA
    assert mock_call.call_count == 2
    assert mock_call.call_args_list[0].kwargs["params"] == {"limit": 1000}
    assert mock_call.call_args_list[1].kwargs["params"] == {
        "limit": 1000,
        "cursor": "cursor-1",
    }


def test_get_accounts_raises_for_missing_account_id_in_filter(mocker):
    mocker.patch(
        "cartography.intel.sentinelone.account.call_sentinelone_api",
        return_value={
            "data": [
                {
                    "name": "Test Account",
                },
            ],
        },
    )

    with pytest.raises(KeyError):
        get_accounts(
            "https://test-api.sentinelone.net",
            "test-api-token",
            account_ids=[ACCOUNT_ID],
        )


def test_get_sites_raises_for_missing_site_id_in_filter(mocker):
    mocker.patch(
        "cartography.intel.sentinelone.account.call_sentinelone_api",
        return_value={
            "data": {
                "sites": [
                    {
                        "accountId": ACCOUNT_ID,
                        "accountName": "Test Account",
                    },
                ],
            },
            "pagination": {},
        },
    )

    with pytest.raises(KeyError):
        get_sites(
            "https://test-api.sentinelone.net",
            "test-api-token",
            site_ids=["site-1"],
        )


def test_get_sites_raises_for_missing_account_id_in_filter(mocker):
    mocker.patch(
        "cartography.intel.sentinelone.account.call_sentinelone_api",
        return_value={
            "data": {
                "sites": [
                    {
                        "id": "site-1",
                        "accountName": "Test Account",
                    },
                ],
            },
            "pagination": {},
        },
    )

    with pytest.raises(KeyError):
        get_sites(
            "https://test-api.sentinelone.net",
            "test-api-token",
            account_ids=[ACCOUNT_ID],
        )
