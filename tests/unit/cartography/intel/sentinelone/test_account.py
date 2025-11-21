from cartography.intel.sentinelone.account import transform_accounts
from tests.data.sentinelone.account import ACCOUNTS_DATA


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
