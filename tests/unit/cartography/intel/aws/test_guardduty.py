from datetime import datetime

from cartography.intel.aws.guardduty import transform_findings
from tests.data.aws.guardduty import GET_FINDINGS

TEST_UPDATE_TAG = 123456789


def test_transform_findings():
    """Test transform_findings function with mock API response data."""
    # Use the full mock API response data
    findings_data = GET_FINDINGS["Findings"]
    transformed = transform_findings(findings_data)

    # Should transform 3 findings
    assert len(transformed) == 3

    # Expected EC2 Instance finding
    expected_ec2_finding = {
        "id": "74b1234567890abcdef1234567890abcdef",
        "arn": "arn:aws:guardduty:us-east-1:123456789012:detector/12abc34d56e78f901234567890abcdef/finding/74b1234567890abcdef1234567890abcdef",
        "type": "UnauthorizedAccess:EC2/MaliciousIPCaller.Custom",
        "severity": 8.0,
        "confidence": 7.5,
        "title": "EC2 instance is communicating with a malicious IP address",
        "description": "EC2 instance i-99999999 is communicating with a malicious IP address 198.51.100.1.",
        "eventfirstseen": datetime(2023, 1, 15, 10, 30, 0),
        "eventlastseen": datetime(2023, 1, 15, 10, 45, 0),
        "accountid": "123456789012",
        "region": "us-east-1",
        "detectorid": "12abc34d56e78f901234567890abcdef",
        "archived": False,
        "resource_type": "Instance",
        "resource_id": "i-99999999",
    }
    assert transformed[0] == expected_ec2_finding

    # Expected S3 Bucket finding
    expected_s3_finding = {
        "id": "85c2345678901bcdef2345678901bcdef0",
        "arn": "arn:aws:guardduty:us-east-1:123456789012:detector/12abc34d56e78f901234567890abcdef/finding/85c2345678901bcdef2345678901bcdef0",
        "type": "Discovery:S3/BucketEnumeration.Unusual",
        "severity": 5.0,
        "confidence": 8.0,
        "title": "S3 bucket is being enumerated from an unusual location",
        "description": "S3 bucket test-bucket is being enumerated from an unusual location.",
        "eventfirstseen": datetime(2023, 1, 16, 14, 20, 0),
        "eventlastseen": datetime(2023, 1, 16, 14, 35, 0),
        "accountid": "123456789012",
        "region": "us-east-1",
        "detectorid": "12abc34d56e78f901234567890abcdef",
        "archived": False,
        "resource_type": "S3Bucket",
        "resource_id": "test-bucket",
    }
    assert transformed[1] == expected_s3_finding

    # Expected IAM AccessKey finding
    expected_iam_finding = {
        "id": "96d3456789012cdef3456789012cdef01",
        "arn": "arn:aws:guardduty:us-east-1:123456789012:detector/12abc34d56e78f901234567890abcdef/finding/96d3456789012cdef3456789012cdef01",
        "type": "PrivilegeEscalation:IAMUser/AnomalousAPIActivity",
        "severity": 7.5,
        "confidence": 6.0,
        "title": "IAM user is making anomalous API calls",
        "description": "IAM user GeneratedFindingUserName is making anomalous API calls.",
        "eventfirstseen": datetime(2023, 1, 17, 9, 15, 0),
        "eventlastseen": datetime(2023, 1, 17, 9, 30, 0),
        "accountid": "123456789012",
        "region": "us-east-1",
        "detectorid": "12abc34d56e78f901234567890abcdef",
        "archived": False,
        "resource_type": "AccessKey",
        "resource_id": None,  # AccessKey doesn't have resource_id
    }
    assert transformed[2] == expected_iam_finding
