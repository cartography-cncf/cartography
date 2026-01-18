from datetime import datetime

# Mock response for list_detectors API call
LIST_DETECTORS = {
    "DetectorIds": [
        "12abc34d56e78f901234567890abcdef",
        "98zyx76w54v32u109876543210zyxwvu",
    ]
}

GET_DETECTOR_DETAILS = [
    {
        "id": "12abc34d56e78f901234567890abcdef",
        "findingpublishingfrequency": "FIFTEEN_MINUTES",
        "service_role": "arn:aws:iam::123456789012:role/aws-service-role/guardduty.amazonaws.com/AWSServiceRoleForAmazonGuardDuty",
        "status": "ENABLED",
        "createdat": datetime(2022, 12, 1, 12, 0, 0),
        "updatedat": datetime(2023, 1, 1, 12, 0, 0),
    },
    {
        "id": "98zyx76w54v32u109876543210zyxwvu",
        "findingpublishingfrequency": "SIX_HOURS",
        "service_role": "arn:aws:iam::123456789012:role/aws-service-role/guardduty.amazonaws.com/AWSServiceRoleForAmazonGuardDutySecondary",
        "status": "DISABLED",
        "createdat": datetime(2022, 11, 1, 9, 0, 0),
        "updatedat": datetime(2022, 12, 1, 9, 0, 0),
    },
]

# Mock response for list_findings API call
LIST_FINDINGS = {
    "FindingIds": [
        "74b1234567890abcdef1234567890abcdef",
        "85c2345678901bcdef2345678901bcdef0",
        "96d3456789012cdef3456789012cdef01",
    ]
}

# Mock response for get_findings API call
GET_FINDINGS = {
    "Findings": [
        {
            "Id": "74b1234567890abcdef1234567890abcdef",
            "Arn": "arn:aws:guardduty:us-east-1:123456789012:detector/12abc34d56e78f901234567890abcdef/finding/74b1234567890abcdef1234567890abcdef",
            "Type": "UnauthorizedAccess:EC2/MaliciousIPCaller.Custom",
            "Title": "EC2 instance is communicating with a malicious IP address",
            "Description": "EC2 instance i-99999999 is communicating with a malicious IP address 198.51.100.1.",
            "Severity": 8.0,
            "Confidence": 7.5,
            "CreatedAt": datetime(2023, 1, 15, 10, 30, 0),
            "UpdatedAt": datetime(2023, 1, 15, 10, 45, 0),
            "EventFirstSeen": datetime(2023, 1, 15, 10, 30, 0),
            "EventLastSeen": datetime(2023, 1, 15, 10, 45, 0),
            "AccountId": "123456789012",
            "Region": "us-east-1",
            "DetectorId": "12abc34d56e78f901234567890abcdef",
            "Archived": False,
            "Resource": {
                "ResourceType": "Instance",
                "InstanceDetails": {
                    "InstanceId": "i-99999999",
                    "InstanceType": "t2.micro",
                    "LaunchTime": datetime(2023, 1, 10, 8, 0, 0),
                    "Platform": "Linux",
                    "ProductCodes": [],
                    "IamInstanceProfile": {
                        "Arn": "arn:aws:iam::123456789012:instance-profile/test-role",
                        "Id": "AIPAI23HZ27SI6FQMGNQ2",
                    },
                    "NetworkInterfaces": [
                        {
                            "Ipv6Addresses": [],
                            "NetworkInterfaceId": "eni-12345678",
                            "PrivateDnsName": "ip-10-0-1-10.ec2.internal",
                            "PrivateIpAddress": "10.0.1.10",
                            "PrivateIpAddresses": [
                                {
                                    "PrivateDnsName": "ip-10-0-1-10.ec2.internal",
                                    "PrivateIpAddress": "10.0.1.10",
                                }
                            ],
                            "PublicDnsName": "ec2-54-123-456-789.compute-1.amazonaws.com",
                            "PublicIp": "54.123.456.789",
                            "SecurityGroups": [
                                {"GroupId": "sg-12345678", "GroupName": "default"}
                            ],
                            "SubnetId": "subnet-12345678",
                            "VpcId": "vpc-12345678",
                        }
                    ],
                    "Tags": [{"Key": "Name", "Value": "test-instance"}],
                },
            },
            "Service": {
                "Action": {
                    "ActionType": "NETWORK_CONNECTION",
                    "NetworkConnectionAction": {
                        "ConnectionDirection": "OUTBOUND",
                        "LocalPortDetails": {"Port": 54321, "PortName": "Unknown"},
                        "Protocol": "TCP",
                        "RemoteIpDetails": {
                            "IpAddressV4": "198.51.100.1",
                            "Country": {
                                "CountryCode": "US",
                                "CountryName": "United States",
                            },
                            "City": {"CityName": "New York"},
                            "GeoLocation": {"Lat": 40.7128, "Lon": -74.0060},
                            "Organization": {
                                "Asn": "12345",
                                "AsnOrg": "Example ISP",
                                "Isp": "Example ISP",
                                "Org": "Example Organization",
                            },
                        },
                        "RemotePortDetails": {"Port": 80, "PortName": "HTTP"},
                    },
                },
                "Archived": False,
                "Count": 5,
                "DetectorId": "12abc34d56e78f901234567890abcdef",
                "EventFirstSeen": datetime(2023, 1, 15, 10, 30, 0),
                "EventLastSeen": datetime(2023, 1, 15, 10, 45, 0),
                "ResourceRole": "TARGET",
                "ServiceName": "guardduty",
            },
        },
        {
            "Id": "85c2345678901bcdef2345678901bcdef0",
            "Arn": "arn:aws:guardduty:us-east-1:123456789012:detector/12abc34d56e78f901234567890abcdef/finding/85c2345678901bcdef2345678901bcdef0",
            "Type": "Discovery:S3/BucketEnumeration.Unusual",
            "Title": "S3 bucket is being enumerated from an unusual location",
            "Description": "S3 bucket test-bucket is being enumerated from an unusual location.",
            "Severity": 5.0,
            "Confidence": 8.0,
            "CreatedAt": datetime(2023, 1, 16, 14, 20, 0),
            "UpdatedAt": datetime(2023, 1, 16, 14, 35, 0),
            "EventFirstSeen": datetime(2023, 1, 16, 14, 20, 0),
            "EventLastSeen": datetime(2023, 1, 16, 14, 35, 0),
            "AccountId": "123456789012",
            "Region": "us-east-1",
            "DetectorId": "12abc34d56e78f901234567890abcdef",
            "Archived": False,
            "Resource": {
                "ResourceType": "S3Bucket",
                "S3BucketDetails": [
                    {
                        "Arn": "arn:aws:s3:::test-bucket",
                        "Name": "test-bucket",
                        "Type": "Destination",
                        "CreatedAt": datetime(2023, 1, 1, 0, 0, 0),
                        "Owner": {"Id": "abcdef1234567890abcdef1234567890abcdef12"},
                        "Tags": [{"Key": "Environment", "Value": "production"}],
                        "DefaultServerSideEncryption": {"EncryptionType": "SSE-S3"},
                        "PublicAccess": {
                            "PermissionConfiguration": {
                                "BucketLevelPermissions": {
                                    "AccessControlList": {
                                        "AllowsPublicReadAccess": False,
                                        "AllowsPublicWriteAccess": False,
                                    },
                                    "BucketPolicy": {
                                        "AllowsPublicReadAccess": False,
                                        "AllowsPublicWriteAccess": False,
                                    },
                                }
                            }
                        },
                    }
                ],
            },
            "Service": {
                "Action": {
                    "ActionType": "AWS_API_CALL",
                    "AwsApiCallAction": {
                        "Api": "ListObjects",
                        "CallerType": "Remote IP",
                        "RemoteIpDetails": {
                            "IpAddressV4": "203.0.113.5",
                            "Country": {"CountryCode": "CA", "CountryName": "Canada"},
                            "City": {"CityName": "Toronto"},
                            "GeoLocation": {"Lat": 43.6532, "Lon": -79.3832},
                            "Organization": {
                                "Asn": "54321",
                                "AsnOrg": "Example Canadian ISP",
                                "Isp": "Example Canadian ISP",
                                "Org": "Example Canadian Organization",
                            },
                        },
                        "ServiceName": "s3.amazonaws.com",
                    },
                },
                "Archived": False,
                "Count": 12,
                "DetectorId": "12abc34d56e78f901234567890abcdef",
                "EventFirstSeen": datetime(2023, 1, 16, 14, 20, 0),
                "EventLastSeen": datetime(2023, 1, 16, 14, 35, 0),
                "ResourceRole": "TARGET",
                "ServiceName": "guardduty",
            },
        },
        {
            "Id": "96d3456789012cdef3456789012cdef01",
            "Arn": "arn:aws:guardduty:us-east-1:123456789012:detector/12abc34d56e78f901234567890abcdef/finding/96d3456789012cdef3456789012cdef01",
            "Type": "PrivilegeEscalation:IAMUser/AnomalousAPIActivity",
            "Title": "IAM user is making anomalous API calls",
            "Description": "IAM user GeneratedFindingUserName is making anomalous API calls.",
            "Severity": 7.5,
            "Confidence": 6.0,
            "CreatedAt": datetime(2023, 1, 17, 9, 15, 0),
            "UpdatedAt": datetime(2023, 1, 17, 9, 30, 0),
            "EventFirstSeen": datetime(2023, 1, 17, 9, 15, 0),
            "EventLastSeen": datetime(2023, 1, 17, 9, 30, 0),
            "AccountId": "123456789012",
            "Region": "us-east-1",
            "DetectorId": "12abc34d56e78f901234567890abcdef",
            "Archived": False,
            "Resource": {
                "ResourceType": "AccessKey",
                "AccessKeyDetails": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "PrincipalId": "AIDACKCEVSQ6C2EXAMPLE",
                    "UserName": "GeneratedFindingUserName",
                    "UserType": "IAMUser",
                },
            },
            "Service": {
                "Action": {
                    "ActionType": "AWS_API_CALL",
                    "AwsApiCallAction": {
                        "Api": "CreateUser",
                        "CallerType": "Remote IP",
                        "RemoteIpDetails": {
                            "IpAddressV4": "192.0.2.1",
                            "Country": {
                                "CountryCode": "US",
                                "CountryName": "United States",
                            },
                            "City": {"CityName": "Seattle"},
                            "GeoLocation": {"Lat": 47.6062, "Lon": -122.3321},
                            "Organization": {
                                "Asn": "16509",
                                "AsnOrg": "AMAZON-02",
                                "Isp": "Amazon.com Inc.",
                                "Org": "Amazon.com Inc.",
                            },
                        },
                        "ServiceName": "iam.amazonaws.com",
                    },
                },
                "Archived": False,
                "Count": 3,
                "DetectorId": "12abc34d56e78f901234567890abcdef",
                "EventFirstSeen": datetime(2023, 1, 17, 9, 15, 0),
                "EventLastSeen": datetime(2023, 1, 17, 9, 30, 0),
                "ResourceRole": "ACTOR",
                "ServiceName": "guardduty",
            },
        },
    ]
}

# Mock findings data for testing transformations
SAMPLE_FINDINGS = [
    {
        "Id": "sample-finding-1",
        "Arn": "arn:aws:guardduty:us-west-2:123456789012:detector/test/finding/sample-finding-1",
        "Type": "UnauthorizedAccess:EC2/MaliciousIPCaller.Custom",
        "Title": "Sample EC2 finding",
        "Description": "Sample description for EC2 instance finding",
        "Severity": 8.0,
        "Confidence": 7.5,
        "Archived": False,
        "Resource": {
            "ResourceType": "Instance",
            "InstanceDetails": {"InstanceId": "i-1234567890abcdef0"},
        },
    },
    {
        "Id": "sample-finding-2",
        "Arn": "arn:aws:guardduty:us-west-2:123456789012:detector/test/finding/sample-finding-2",
        "Type": "Discovery:S3/BucketEnumeration.Unusual",
        "Title": "Sample S3 finding",
        "Description": "Sample description for S3 bucket finding",
        "Severity": 5.0,
        "Archived": False,
        "Resource": {
            "ResourceType": "S3Bucket",
            "S3BucketDetails": [{"Name": "sample-test-bucket"}],
        },
    },
    {
        "Id": "sample-finding-3-archived",
        "Arn": "arn:aws:guardduty:us-west-2:123456789012:detector/test/finding/sample-finding-3-archived",
        "Type": "UnauthorizedAccess:EC2/MaliciousIPCaller.Custom",
        "Title": "Sample archived finding",
        "Description": "Sample description for archived finding that should be filtered out",
        "Severity": 9.0,
        "Confidence": 8.5,
        "Archived": True,
        "Resource": {
            "ResourceType": "Instance",
            "InstanceDetails": {"InstanceId": "i-archived123456789"},
        },
    },
]

# Expected transform results for test_transform_findings
EXPECTED_TRANSFORM_RESULTS = [
    # Expected EC2 Instance finding
    {
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
    },
    # Expected S3 Bucket finding
    {
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
    },
    # Expected IAM AccessKey finding
    {
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
    },
]
