from cartography.intel.aws import guardduty
from tests.data.aws import guardduty as test_data


def test_transform_guardduty_findings():
    results = guardduty.transform_guardduty_findings(test_data.FINDINGS)
    assert results == [
        {
            "id": "finding-1",
            "arn": "arn:aws:guardduty:us-east-1:111111111111:detector/det123/finding/finding-1",
            "type": "Recon:EC2/PortProbeUnprotectedPort",
            "severity": 5.3,
            "title": "Port probe",
            "description": "Unprotected port found",
            "resource_type": "Instance",
            "resource_id": "i-abc123",
        },
        {
            "id": "finding-2",
            "arn": "arn:aws:guardduty:us-east-1:111111111111:detector/det123/finding/finding-2",
            "type": "Recon:S3/BucketEnumeration",
            "severity": 3.2,
            "title": "S3 bucket enumeration",
            "description": "Bucket enumeration attempt",
            "resource_type": "S3Bucket",
            "resource_id": "my-bucket",
        },
    ]
