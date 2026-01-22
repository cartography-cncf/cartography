AGENT_ID = "test-s1-agent-123"
AGENT_ID_2 = "test-s1-agent-456"
AGENT_ID_3 = "test-s1-agent-789"

AGENTS_DATA = [
    {
        "id": AGENT_ID,
        "uuid": "uuid-123-456-789",
        "computerName": "test-computer-01",
        "firewallEnabled": True,
        "osName": "Windows 10",
        "osRevision": "1909",
        "domain": "test.local",
        "lastActiveDate": "2023-12-01T10:00:00Z",
        "lastSuccessfulScanDate": "2023-12-01T09:00:00Z",
        "scanStatus": "finished",
        "serialNumber": "SN123456",
    },
    {
        "id": AGENT_ID_2,
        "uuid": "uuid-456-789-123",
        "computerName": "test-computer-02",
        "firewallEnabled": False,
        "osName": "Ubuntu 20.04",
        "osRevision": "5.4.0-89-generic",
        "domain": "test.local",
        "lastActiveDate": "2023-12-01T11:00:00Z",
        "lastSuccessfulScanDate": "2023-12-01T10:30:00Z",
        "scanStatus": "finished",
        "serialNumber": "SN789012",
    },
    {
        "id": AGENT_ID_3,
        "uuid": "uuid-789-123-456",
        "computerName": "test-computer-03",
        "firewallEnabled": True,
        "osName": "macOS",
        "osRevision": "12.6.1",
        "domain": None,  # No domain for macOS
        "lastActiveDate": "2023-12-01T12:00:00Z",
        "lastSuccessfulScanDate": None,  # Never completed scan
        "scanStatus": "in_progress",
        "serialNumber": "SN345678",
    },
]

# Test data for minimal required fields only
AGENTS_DATA_MINIMAL = [
    {
        "id": "minimal-agent-001",
        # All other fields missing - should be handled gracefully
    },
]

# Test data for paginated API responses
AGENTS_PAGINATED_PAGE_1 = {
    "data": [AGENTS_DATA[0], AGENTS_DATA[1]],
    "pagination": {
        "nextCursor": "cursor-page-2",
        "totalItems": 3,
    },
}

AGENTS_PAGINATED_PAGE_2 = {
    "data": [AGENTS_DATA[2]],
    "pagination": {
        "nextCursor": None,
        "totalItems": 3,
    },
}

# Mock API responses
MOCK_AGENTS_API_RESPONSE = {
    "data": AGENTS_DATA,
    "pagination": {
        "nextCursor": None,
        "totalItems": 3,
    },
}

MOCK_AGENTS_API_RESPONSE_EMPTY = {
    "data": [],
    "pagination": {
        "nextCursor": None,
        "totalItems": 0,
    },
}

# Account ID for testing relationships
TEST_ACCOUNT_ID = "test-s1-account-123"
