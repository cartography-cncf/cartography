FINDINGS = [
    {
        "Id": "finding-1",
        "Arn": "arn:aws:guardduty:us-east-1:111111111111:detector/det123/finding/finding-1",
        "Type": "Recon:EC2/PortProbeUnprotectedPort",
        "Severity": 5.3,
        "Title": "Port probe",
        "Description": "Unprotected port found",
        "Resource": {
            "ResourceType": "Instance",
            "InstanceDetails": {"InstanceId": "i-abc123"},
        },
    },
    {
        "Id": "finding-2",
        "Arn": "arn:aws:guardduty:us-east-1:111111111111:detector/det123/finding/finding-2",
        "Type": "Recon:S3/BucketEnumeration",
        "Severity": 3.2,
        "Title": "S3 bucket enumeration",
        "Description": "Bucket enumeration attempt",
        "Resource": {
            "ResourceType": "S3Bucket",
            "S3BucketDetails": [{"Name": "my-bucket"}],
        },
    },
]
