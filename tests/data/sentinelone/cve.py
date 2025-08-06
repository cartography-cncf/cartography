CVE_ID_1 = "cve-test-123"
CVE_ID_2 = "cve-test-456"
CVE_ID_3 = "cve-test-789"

# Test data for CVEs from SentinelOne API
CVES_DATA = [
    {
        "id": CVE_ID_1,
        "cveId": "CVE-2023-1234",
        "baseScore": 7.5,
        "cvssVersion": "3.1",
        "daysDetected": 45,
        "detectionDate": "2023-11-01T10:00:00Z",
        "lastScanDate": "2023-12-15T14:30:00Z",
        "lastScanResult": "vulnerable",
        "publishedDate": "2023-10-15T00:00:00Z",
        "severity": "High",
        "status": "active",
        "applicationName": "OpenSSL",
        "applicationVendor": "OpenSSL Foundation",
        "applicationVersion": "1.1.1k",
    },
    {
        "id": CVE_ID_2,
        "cveId": "CVE-2023-5678",
        "baseScore": 9.8,
        "cvssVersion": "3.1",
        "daysDetected": 12,
        "detectionDate": "2023-12-01T08:45:00Z",
        "lastScanDate": "2023-12-15T16:20:00Z",
        "lastScanResult": "vulnerable",
        "publishedDate": "2023-11-20T00:00:00Z",
        "severity": "Critical",
        "status": "active",
        "applicationName": "Apache HTTP Server",
        "applicationVendor": "Apache Software Foundation",
        "applicationVersion": "2.4.41",
    },
    {
        "id": CVE_ID_3,
        "cveId": "CVE-2023-9012",
        "baseScore": 5.3,
        "cvssVersion": "3.1",
        "daysDetected": 90,
        "detectionDate": "2023-09-15T12:00:00Z",
        "lastScanDate": "2023-12-15T09:15:00Z",
        "lastScanResult": "patched",
        "publishedDate": "2023-08-30T00:00:00Z",
        "severity": "Medium",
        "status": "resolved",
        "applicationName": "Node.js",
        "applicationVendor": "Node.js Foundation",
        "applicationVersion": "16.14.2",
    },
]

# Test data with minimal required fields only
CVES_DATA_MINIMAL = [
    {
        "id": "minimal-cve-001",
        "cveId": "CVE-2023-0001",
        # All other fields missing - should be handled gracefully
    },
]

# Test data with missing required fields (should cause errors)
CVES_DATA_INVALID = [
    {
        # Missing "id" field - should fail
        "cveId": "CVE-2023-BAD1",
        "severity": "High",
    },
    {
        "id": "bad-cve-002",
        # Missing "cveId" field - should fail
        "severity": "Medium",
    },
]

# Mock API response structure
MOCK_CVES_API_RESPONSE = {
    "data": CVES_DATA,
    "pagination": {
        "nextCursor": None,
        "totalItems": 3,
    },
}

MOCK_CVES_API_RESPONSE_EMPTY = {
    "data": [],
    "pagination": {
        "nextCursor": None,
        "totalItems": 0,
    },
}

# Account ID for testing relationships
TEST_ACCOUNT_ID = "test-s1-account-123"

# Common job parameters for testing
TEST_UPDATE_TAG = 123456789
TEST_API_URL = "https://test-api.sentinelone.net"
TEST_API_TOKEN = "test-api-token"

TEST_COMMON_JOB_PARAMETERS = {
    "UPDATE_TAG": TEST_UPDATE_TAG,
    "API_URL": TEST_API_URL,
    "API_TOKEN": TEST_API_TOKEN,
    "S1_ACCOUNT_ID": TEST_ACCOUNT_ID,
}
