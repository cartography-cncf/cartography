ACCOUNT_ID = "test-s1-account-123"
ACCOUNT_ID_2 = "test-s1-account-456"
ACCOUNT_ID_3 = "test-s1-account-789"
SITE_ID = "test-s1-site-123"
SITE_ID_2 = "test-s1-site-456"
SITE_ID_3 = "test-s1-site-789"
ACCOUNTS_DATA = [
    {
        "id": ACCOUNT_ID,
        "accountType": "Trial",
        "activeAgents": 1,
        "createdAt": "2023-01-01T00:00:00Z",
        "expiration": "2025-01-01T00:00:00Z",
        "name": "Test Account",
        "numberOfSites": 1,
        "state": "Active",
    },
    {
        "id": ACCOUNT_ID_2,
        "accountType": "Trial",
        "activeAgents": 1,
        "createdAt": "2023-01-01T00:00:00Z",
        "expiration": "2025-01-01T00:00:00Z",
        "name": "Test Account 2",
        "numberOfSites": 1,
        "state": "Active",
    },
    {
        "id": ACCOUNT_ID_3,
        "accountType": "Trial",
        "activeAgents": 1,
        "createdAt": "2023-01-01T00:00:00Z",
        "expiration": "2025-01-01T00:00:00Z",
        "name": "Test Account 3",
        "numberOfSites": 1,
        "state": "Active",
    },
]

SITES_DATA = [
    {
        "id": SITE_ID,
        "name": "Test Site",
        "accountId": ACCOUNT_ID,
        "accountName": "Test Account",
        "activeLicenses": 3,
        "createdAt": "2023-01-01T00:00:00Z",
        "expiration": "2025-01-01T00:00:00Z",
        "state": "active",
    },
    {
        "id": SITE_ID_2,
        "name": "Test Site 2",
        "accountId": ACCOUNT_ID,
        "accountName": "Test Account",
        "activeLicenses": 2,
        "createdAt": "2023-01-01T00:00:00Z",
        "expiration": "2025-01-01T00:00:00Z",
        "state": "active",
    },
    {
        "id": SITE_ID_3,
        "name": "Test Site 3",
        "accountId": ACCOUNT_ID_2,
        "accountName": "Test Account 2",
        "activeLicenses": 1,
        "createdAt": "2023-01-02T00:00:00Z",
        "expiration": "2025-01-02T00:00:00Z",
        "state": "active",
    },
]
