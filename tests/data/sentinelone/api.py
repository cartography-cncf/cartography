# Test data for SentinelOne API module

# Base API configuration
TEST_API_URL = "https://test-api.sentinelone.net"
TEST_API_TOKEN = "test-api-token-123"
TEST_ENDPOINT = "web/api/v2.1/test"

# Mock API responses for call_sentinelone_api function
MOCK_API_RESPONSE_SUCCESS = {
    "data": [
        {"id": "item-1", "name": "Test Item 1"},
        {"id": "item-2", "name": "Test Item 2"},
    ],
    "pagination": {
        "nextCursor": None,
        "totalItems": 2,
    },
}

# Paginated API responses for get_paginated_results function
MOCK_PAGINATED_RESPONSE_PAGE_1 = {
    "data": [
        {"id": "item-1", "name": "Test Item 1"},
        {"id": "item-2", "name": "Test Item 2"},
    ],
    "pagination": {
        "nextCursor": "cursor-page-2",
        "totalItems": 4,
    },
}

MOCK_PAGINATED_RESPONSE_PAGE_2 = {
    "data": [
        {"id": "item-3", "name": "Test Item 3"},
        {"id": "item-4", "name": "Test Item 4"},
    ],
    "pagination": {
        "nextCursor": None,
        "totalItems": 4,
    },
}

# Expected combined result from pagination
EXPECTED_PAGINATED_RESULT = [
    {"id": "item-1", "name": "Test Item 1"},
    {"id": "item-2", "name": "Test Item 2"},
    {"id": "item-3", "name": "Test Item 3"},
    {"id": "item-4", "name": "Test Item 4"},
]

# Test parameters
TEST_PARAMS = {
    "accountIds": "test-account-123",
    "limit": 100,
}

# Test data for different pagination scenarios
MOCK_SINGLE_PAGE_RESPONSE = {
    "data": [
        {"id": "single-item", "name": "Single Item"},
    ],
    "pagination": {
        "nextCursor": None,
        "totalItems": 1,
    },
}

MOCK_EMPTY_PAGINATION_RESPONSE = {
    "data": [],
    "pagination": {
        "nextCursor": None,
        "totalItems": 0,
    },
}
