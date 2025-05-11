import datetime

DESCRIBE_INSTANCES = {
    "NextToken": "INSERT_TOKEN_HERE",
    "Reservations": [
        {
            "Groups": [],
            "Instances": [
                {
                    "AmiLaunchIndex": 0,
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "AttachTime": datetime.datetime(
                                    2018, 10, 14, 16, 30, 26
                                ),
                                "DeleteOnTermination": True,
                                "Status": "attached",
                                "VolumeId": "vol-0df",
                            },
                        }
                    ],
                    "CapacityReservationSpecification": {
                        "CapacityReservationPreference": "open",
                    },
                    "ClientToken": "SOME_TOKEN",
                    "CpuOptions": {
                        "CoreCount": 1,
                        "ThreadsPerCore": 2,
                    },
                    "EbsOptimized": False,
                    "HibernationOptions": {
                        "Configured": False,
                    },
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                        "Arn": "arn:aws:iam::000000000000:instance-profile/PROFILE_NAME",
                        "Id": "PROFILE_NAME",
                    },
                    "ImageId": "IMAGE_ID",
                    "InstanceId": "i-01",
                    "InstanceType": "c4.large",
                    "KeyName": "boot",
                    "LaunchTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
                    "Monitoring": {
                        "State": "enabled",
                    },
                    "NetworkInterfaces": [
                        {
                            "Association": {
                                "IpOwnerId": "amazon",
                                "PublicDnsName": "ec2-123-123-123-123.compute-1.amazonaws.com",
                                "PublicIp": "123.123.123.123",
                            },
                            "Attachment": {
                                "AttachTime": datetime.datetime(
                                    2018, 10, 14, 16, 30, 26
                                ),
                                "AttachmentId": "ATTACHMENT_ID",
                                "DeleteOnTermination": True,
                                "DeviceIndex": 0,
                                "Status": "attached",
                            },
                            "Description": "",
                            "Groups": [
                                {
                                    "GroupId": "sg-GROUP-ID",
                                    "GroupName": "SOME_GROUP_ID",
                                },
                                {
                                    "GroupId": "SOME_GROUP_ID_2",
                                    "GroupName": "MY_GROUP_NAME_2",
                                },
                            ],
                            "Ipv6Addresses": [],
                            "MacAddress": "00:00:00:00:00:01",
                            "NetworkInterfaceId": "eni-de",
                            "OwnerId": "OWNER_ACCOUNT_ID",
                            "PrivateDnsName": "ip-345-345-345-345.ec2.internal",
                            "PrivateIpAddress": "345.345.345.345",
                            "PrivateIpAddresses": [
                                {
                                    "Association": {
                                        "IpOwnerId": "amazon",
                                        "PublicDnsName": "ec2-234-234-234-234.compute-1.amazonaws.com",
                                        "PublicIp": "234.234.234.234",
                                    },
                                    "Primary": True,
                                    "PrivateDnsName": "ip-345-345-345-345.ec2.internal",
                                    "PrivateIpAddress": "345.345.345.345",
                                }
                            ],
                            "SourceDestCheck": True,
                            "Status": "in-use",
                            # SubnetId is set to None intentionally on this NIC.
                            # The AWS APIs return None on subnetids intermittently.
                            "SubnetId": None,
                            "VpcId": "SOME_VPC_ID",
                        }
                    ],
                    "Placement": {
                        "AvailabilityZone": "us-east-1d",
                        "GroupName": "",
                        "Tenancy": "default",
                    },
                    "PrivateDnsName": "ip-345-345-345-345.ec2.internal",
                    "PrivateIpAddress": "345.345.345.345",
                    "ProductCodes": [],
                    "PublicDnsName": "ec2-234-234-234-234.compute-1.amazonaws.com",
                    "PublicIpAddress": "234.234.234.234",
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                        {
                            "GroupId": "sg-GROUP-ID",
                            "GroupName": "SOME_GROUP_ID",
                        },
                        {
                            "GroupId": "SOME_GROUP_ID_2",
                            "GroupName": "MY_GROUP_NAME_2",
                        },
                    ],
                    "SourceDestCheck": True,
                    "State": {
                        "Code": 16,
                        "Name": "running",
                    },
                    "StateTransitionReason": "",
                    # SubnetId is set to None intentionally on this instance.
                    "SubnetId": None,
                    "Tags": [
                        {
                            "Key": "aws:autoscaling:groupName",
                            "Value": "MY_SERVICE_NAME",
                        },
                        {
                            "Key": "Name",
                            "Value": "MY_SERVICE_NAME",
                        },
                    ],
                    "VirtualizationType": "hvm",
                    "VpcId": "SOME_VPC_ID",
                }
            ],
            "OwnerId": "OWNER_ACCOUNT_ID",
            "RequesterId": "REQUESTER_ID",
            "ReservationId": "r-01",
        },
        {
            "Groups": [],
            "Instances": [
                {
                    "AmiLaunchIndex": 0,
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "AttachTime": datetime.datetime(
                                    2018, 10, 14, 16, 30, 26
                                ),
                                "DeleteOnTermination": True,
                                "Status": "attached",
                                "VolumeId": "vol-03",
                            },
                        }
                    ],
                    "CapacityReservationSpecification": {
                        "CapacityReservationPreference": "open",
                    },
                    "ClientToken": "SOME_GUID",
                    "CpuOptions": {
                        "CoreCount": 1,
                        "ThreadsPerCore": 2,
                    },
                    "EbsOptimized": False,
                    "HibernationOptions": {
                        "Configured": False,
                    },
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                        "Arn": "arn:aws:iam::000000000000:instance-profile/SERVICE_NAME_2",
                        "Id": "SERVICE_NAME_2",
                    },
                    "ImageId": "ami-2c",
                    "InstanceId": "i-02",
                    "InstanceType": "c4.large",
                    "KeyName": "boot",
                    "LaunchTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
                    "Monitoring": {
                        "State": "enabled",
                    },
                    "NetworkInterfaces": [
                        {
                            "Association": {
                                "IpOwnerId": "amazon",
                                "PublicDnsName": "ec2-456-456-456-456.compute-1.amazonaws.com",
                                "PublicIp": "456.456.456.456",
                            },
                            "Attachment": {
                                "AttachTime": datetime.datetime(
                                    2018, 10, 14, 16, 30, 26
                                ),
                                "AttachmentId": "eni-attach-b2",
                                "DeleteOnTermination": True,
                                "DeviceIndex": 0,
                                "Status": "attached",
                            },
                            "Description": "",
                            "Groups": [
                                {
                                    "GroupId": "SOME_GROUP_ID_2",
                                    "GroupName": "MY_GROUP_NAME_2",
                                },
                                {
                                    "GroupId": "SOME_GROUP_ID_3",
                                    "GroupName": "SERVICE_NAME_2",
                                },
                            ],
                            "Ipv6Addresses": [],
                            "MacAddress": "00:00:00:00:00:02",
                            "NetworkInterfaceId": "eni-87",
                            "OwnerId": "OWNER_ACCOUNT_ID",
                            "PrivateDnsName": "ip-567-567-567-567.ec2.internal",
                            "PrivateIpAddress": "567.567.567.567",
                            "PrivateIpAddresses": [
                                {
                                    "Association": {
                                        "IpOwnerId": "amazon",
                                        "PublicDnsName": "ec2-456-456-456-456.compute-1.amazonaws.com",
                                        "PublicIp": "456.456.456.456",
                                    },
                                    "Primary": True,
                                    "PrivateDnsName": "ip-567-567-567-567.ec2.internal",
                                    "PrivateIpAddress": "567.567.567.567",
                                }
                            ],
                            "SourceDestCheck": True,
                            "Status": "in-use",
                            "SubnetId": "SOME_SUBNET_1",
                            "VpcId": "SOME_VPC_ID",
                        }
                    ],
                    "Placement": {
                        "AvailabilityZone": "us-east-1d",
                        "GroupName": "",
                        "Tenancy": "default",
                    },
                    "PrivateDnsName": "ip-567-567-567-567.ec2.internal",
                    "PrivateIpAddress": "567.567.567.567",
                    "ProductCodes": [],
                    "PublicDnsName": "ec2-456-456-456-456.compute-1.amazonaws.com",
                    "PublicIpAddress": "456.456.456.456",
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                        {
                            "GroupId": "SOME_GROUP_ID_2",
                            "GroupName": "MY_GROUP_NAME_2",
                        },
                        {
                            "GroupId": "SOME_GROUP_ID_3",
                            "GroupName": "SERVICE_NAME_2",
                        },
                    ],
                    "SourceDestCheck": True,
                    "State": {
                        "Code": 16,
                        "Name": "running",
                    },
                    "StateTransitionReason": "",
                    "SubnetId": "SOME_SUBNET_1",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "MY_OTHER_SERVICE_NAME",
                        },
                        {
                            "Key": "aws:autoscaling:groupName",
                            "Value": "MY_OTHER_SERVICE_NAME",
                        },
                    ],
                    "VirtualizationType": "hvm",
                    "VpcId": "SOME_VPC_ID",
                }
            ],
            "OwnerId": "OWNER_ACCOUNT_ID",
            "RequesterId": "REQUESTER_ID",
            "ReservationId": "r-02",
        },
        {
            "Groups": [],
            "Instances": [
                {
                    "AmiLaunchIndex": 0,
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "AttachTime": datetime.datetime(
                                    2018,
                                    10,
                                    14,
                                    16,
                                    30,
                                    26,
                                ),
                                "DeleteOnTermination": True,
                                "Status": "attached",
                                "VolumeId": "vol-09",
                            },
                        }
                    ],
                    "CapacityReservationSpecification": {
                        "CapacityReservationPreference": "open",
                    },
                    "ClientToken": "ANOTHER_GUID",
                    "CpuOptions": {
                        "CoreCount": 1,
                        "ThreadsPerCore": 2,
                    },
                    "EbsOptimized": False,
                    "HibernationOptions": {
                        "Configured": False,
                    },
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                        "Arn": "arn:aws:iam::000000000000:instance-profile/ANOTHER_SERVICE_NAME",
                        "Id": "ANOTHER_SERVICE_NAME",
                    },
                    "ImageId": "THIS_IS_AN_IMAGE_ID",
                    "InstanceId": "i-03",
                    "InstanceType": "r4.large",
                    "KeyName": "boot",
                    "LaunchTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
                    "Monitoring": {
                        "State": "enabled",
                    },
                    "NetworkInterfaces": [
                        {
                            "Association": {
                                "IpOwnerId": "amazon",
                                "PublicDnsName": "ec2-678-678-678-678.compute-1.amazonaws.com",
                                "PublicIp": "678.678.678.678",
                            },
                            "Attachment": {
                                "AttachTime": datetime.datetime(
                                    2018,
                                    10,
                                    14,
                                    16,
                                    30,
                                    26,
                                ),
                                "AttachmentId": "eni-attach-c4",
                                "DeleteOnTermination": True,
                                "DeviceIndex": 0,
                                "Status": "attached",
                            },
                            "Description": "",
                            "Groups": [
                                {
                                    "GroupId": "SOME_GROUP_ID_2",
                                    "GroupName": "MY_GROUP_NAME_2",
                                },
                                {
                                    "GroupId": "THIS_IS_A_SG_ID",
                                    "GroupName": "THIS_IS_A_SERVICE_NAME",
                                },
                            ],
                            "Ipv6Addresses": [],
                            "MacAddress": "00:00:00:00:00:03",
                            "NetworkInterfaceId": "eni-75",
                            "OwnerId": "OWNER_ACCOUNT_ID",
                            "PrivateDnsName": "ip-789-789-789-789.ec2.internal",
                            "PrivateIpAddress": "789.789.789.789",
                            "PrivateIpAddresses": [
                                {
                                    "Association": {
                                        "IpOwnerId": "amazon",
                                        "PublicDnsName": "ec2-678-678-678-678.compute-1.amazonaws.com",
                                        "PublicIp": "678.678.678.678",
                                    },
                                    "Primary": True,
                                    "PrivateDnsName": "ip-789-789-789-789.ec2.internal",
                                    "PrivateIpAddress": "789.789.789.789",
                                }
                            ],
                            "SourceDestCheck": True,
                            "Status": "in-use",
                            "SubnetId": "SOME_SUBNET_1",
                            "VpcId": "SOME_VPC_ID",
                        }
                    ],
                    "Placement": {
                        "AvailabilityZone": "us-east-1d",
                        "GroupName": "",
                        "Tenancy": "default",
                    },
                    "PrivateDnsName": "ip-789-789-789-789.ec2.internal",
                    "PrivateIpAddress": "789.789.789.789",
                    "ProductCodes": [],
                    "PublicDnsName": "ec2-678-678-678-678.compute-1.amazonaws.com",
                    "PublicIpAddress": "678.678.678.678",
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                        {
                            "GroupId": "SOME_GROUP_ID_2",
                            "GroupName": "MY_GROUP_NAME_2",
                        },
                        {
                            "GroupId": "THIS_IS_A_SG_ID",
                            "GroupName": "THIS_IS_A_SERVICE_NAME",
                        },
                    ],
                    "SourceDestCheck": True,
                    "State": {
                        "Code": 16,
                        "Name": "running",
                    },
                    "StateTransitionReason": "",
                    "SubnetId": "SOME_SUBNET_1",
                    "Tags": [
                        {
                            "Key": "Name",
                            "Value": "PREFIX__ANOTHER_SERVICE_NAME",
                        },
                        {
                            "Key": "aws:autoscaling:groupName",
                            "Value": "PREFIX__ANOTHER_SERVICE_NAME",
                        },
                    ],
                    "VirtualizationType": "hvm",
                    "VpcId": "SOME_VPC_ID",
                },
                {
                    "AmiLaunchIndex": 2,
                    "Architecture": "x86_64",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/sda1",
                            "Ebs": {
                                "AttachTime": datetime.datetime(
                                    2018,
                                    10,
                                    14,
                                    16,
                                    30,
                                    26,
                                ),
                                "DeleteOnTermination": True,
                                "Status": "attached",
                                "VolumeId": "vol-04",
                            },
                        }
                    ],
                    "CapacityReservationSpecification": {
                        "CapacityReservationPreference": "open",
                    },
                    "ClientToken": "HI_THIS_IS_A_GUID",
                    "CpuOptions": {
                        "CoreCount": 1,
                        "ThreadsPerCore": 2,
                    },
                    "EbsOptimized": False,
                    "HibernationOptions": {
                        "Configured": False,
                    },
                    "Hypervisor": "xen",
                    "IamInstanceProfile": {
                        "Arn": "arn:aws:iam::000000000000:instance-profile/ANOTHER_SERVICE_NAME",
                        "Id": "ANOTHER_SERVICE_NAME",
                    },
                    "ImageId": "THIS_IS_AN_IMAGE_ID",
                    "InstanceId": "i-04",
                    "InstanceType": "r4.large",
                    "KeyName": "boot",
                    "LaunchTime": datetime.datetime(2018, 10, 14, 16, 30, 26),
                    "Monitoring": {
                        "State": "enabled",
                    },
                    "NetworkInterfaces": [
                        {
                            "Association": {
                                "IpOwnerId": "amazon",
                                "PublicDnsName": "ec2-12-12-12-12.compute-1.amazonaws.com",
                                "PublicIp": "12.12.12.12",
                            },
                            "Attachment": {
                                "AttachTime": datetime.datetime(
                                    2018,
                                    10,
                                    14,
                                    16,
                                    30,
                                    26,
                                ),
                                "AttachmentId": "eni-attach-ca",
                                "DeleteOnTermination": True,
                                "DeviceIndex": 0,
                                "Status": "attached",
                            },
                            "Description": "",
                            "Groups": [
                                {
                                    "GroupId": "SOME_GROUP_ID_2",
                                    "GroupName": "MY_GROUP_NAME_2",
                                },
                                {
                                    "GroupId": "THIS_IS_A_SG_ID",
                                    "GroupName": "THIS_IS_A_SERVICE_NAME",
                                },
                            ],
                            "Ipv6Addresses": [],
                            "MacAddress": "00:00:00:00:00:05",
                            "NetworkInterfaceId": "eni-76",
                            "OwnerId": "OWNER_ACCOUNT_ID",
                            "PrivateDnsName": "ip-23-23-23-23.ec2.internal",
                            "PrivateIpAddress": "23.23.23.23",
                            "PrivateIpAddresses": [
                                {
                                    "Association": {
                                        "IpOwnerId": "amazon",
                                        "PublicDnsName": "ec2-12-12-12-12.compute-1.amazonaws.com",
                                        "PublicIp": "12.12.12.12",
                                    },
                                    "Primary": True,
                                    "PrivateDnsName": "ip-23-23-23-23.ec2.internal",
                                    "PrivateIpAddress": "23.23.23.23",
                                }
                            ],
                            "SourceDestCheck": True,
                            "Status": "in-use",
                            "SubnetId": "SOME_SUBNET_1",
                            "VpcId": "SOME_VPC_ID",
                        }
                    ],
                    "Placement": {
                        "AvailabilityZone": "us-east-1d",
                        "GroupName": "",
                        "Tenancy": "default",
                    },
                    "PrivateDnsName": "ip-23-23-23-23.ec2.internal",
                    "PrivateIpAddress": "23.23.23.23",
                    "ProductCodes": [],
                    "PublicDnsName": "ec2-12-12-12-12.compute-1.amazonaws.com",
                    "PublicIpAddress": "12.12.12.12",
                    "RootDeviceName": "/dev/sda1",
                    "RootDeviceType": "ebs",
                    "SecurityGroups": [
                        {
                            "GroupId": "SOME_GROUP_ID_2",
                            "GroupName": "MY_GROUP_NAME_2",
                        },
                        {
                            "GroupId": "THIS_IS_A_SG_ID",
                            "GroupName": "THIS_IS_A_SERVICE_NAME",
                        },
                    ],
                    "SourceDestCheck": True,
                    "State": {
                        "Code": 16,
                        "Name": "running",
                    },
                    "StateTransitionReason": "",
                    "SubnetId": "SOME_SUBNET_1",
                    "Tags": [
                        {
                            "Key": "aws:autoscaling:groupName",
                            "Value": "PREFIX__ANOTHER_SERVICE_NAME",
                        },
                        {
                            "Key": "Name",
                            "Value": "PREFIX__ANOTHER_SERVICE_NAME",
                        },
                    ],
                    "VirtualizationType": "hvm",
                    "VpcId": "SOME_VPC_ID",
                },
            ],
            "OwnerId": "OWNER_ACCOUNT_ID",
            "RequesterId": "REQUESTER_ID",
            "ReservationId": "r-03",
        },
    ],
    "ResponseMetadata": {
        "HTTPHeaders": {
            "content-type": "text/xml;charset=UTF-8",
            "date": "Wed, 15 Jan 2020 18:51:47 GMT",
            "server": "AmazonEC2",
            "transfer-encoding": "chunked",
            "vary": "accept-encoding",
        },
        "HTTPStatusCode": 200,
        "RequestId": "REQUEST_ID",
        "RetryAttempts": 0,
    },
}


INSTANCE_WITH_IAM_PROFILE = [
    {
        "ReservationId": "r-04e",
        "OwnerId": "1234",
        "Groups": [],
        "Instances": [
            {
                "Architecture": "x86_64",
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/xvda",
                        "Ebs": {
                            "AttachTime": datetime.datetime(2024, 12, 21, 7, 28, 25),
                            "DeleteOnTermination": True,
                            "Status": "attached",
                            "VolumeId": "vol-086",
                        },
                    },
                ],
                "ClientToken": "5669c797",
                "EbsOptimized": False,
                "EnaSupport": True,
                "Hypervisor": "xen",
                "IamInstanceProfile": {
                    "Arn": "arn:aws:iam::1234:instance-profile/cartography-service",
                    "Id": "AIPA",
                },
                "NetworkInterfaces": [
                    {
                        "Association": {
                            "IpOwnerId": "amazon",
                            "PublicDnsName": "ec2-1-2-3-4.compute-1.amazonaws.com",
                            "PublicIp": "1.2.3.4",
                        },
                        "Attachment": {
                            "AttachTime": datetime.datetime(2024, 12, 21, 7, 28, 24),
                            "AttachmentId": "eni-attach-00e3",
                            "DeleteOnTermination": True,
                            "DeviceIndex": 0,
                            "Status": "attached",
                            "NetworkCardIndex": 0,
                        },
                        "Description": "",
                        "Groups": [
                            {
                                "GroupId": "sg-050",
                                "GroupName": "launch-wizard-1",
                            },
                        ],
                        "Ipv6Addresses": [],
                        "MacAddress": "12:33:9f:44:88:d3",
                        "NetworkInterfaceId": "eni-0ba",
                        "OwnerId": "1234",
                        "PrivateDnsName": "ip-172-31-81-190.ec2.internal",
                        "PrivateIpAddress": "172.31.81.190",
                        "PrivateIpAddresses": [
                            {
                                "Association": {
                                    "IpOwnerId": "amazon",
                                    "PublicDnsName": "ec2-1-2-3-4.compute-1.amazonaws.com",
                                    "PublicIp": "1.2.3.4",
                                },
                                "Primary": True,
                                "PrivateDnsName": "ip-172-31-81-190.ec2.internal",
                                "PrivateIpAddress": "172.31.81.190",
                            },
                        ],
                        "SourceDestCheck": True,
                        "Status": "in-use",
                        "SubnetId": "subnet-0c9",
                        "VpcId": "vpc-05b",
                        "InterfaceType": "interface",
                        "Operator": {
                            "Managed": False,
                        },
                    },
                ],
                "RootDeviceName": "/dev/xvda",
                "RootDeviceType": "ebs",
                "SecurityGroups": [
                    {
                        "GroupId": "sg-050",
                        "GroupName": "launch-wizard-1",
                    },
                ],
                "SourceDestCheck": True,
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": "micro-wizard",
                    },
                ],
                "VirtualizationType": "hvm",
                "CpuOptions": {
                    "CoreCount": 1,
                    "ThreadsPerCore": 1,
                },
                "CapacityReservationSpecification": {
                    "CapacityReservationPreference": "open",
                },
                "HibernationOptions": {
                    "Configured": False,
                },
                "MetadataOptions": {
                    "State": "applied",
                    "HttpTokens": "required",
                    "HttpPutResponseHopLimit": 2,
                    "HttpEndpoint": "enabled",
                    "HttpProtocolIpv6": "disabled",
                    "InstanceMetadataTags": "disabled",
                },
                "EnclaveOptions": {
                    "Enabled": False,
                },
                "BootMode": "uefi-preferred",
                "PlatformDetails": "Linux/UNIX",
                "UsageOperation": "RunInstances",
                "UsageOperationUpdateTime": datetime.datetime(2024, 12, 21, 7, 28, 24),
                "PrivateDnsNameOptions": {
                    "HostnameType": "ip-name",
                    "EnableResourceNameDnsARecord": True,
                    "EnableResourceNameDnsAAAARecord": False,
                },
                "MaintenanceOptions": {
                    "AutoRecovery": "default",
                },
                "CurrentInstanceBootMode": "legacy-bios",
                "NetworkPerformanceOptions": {
                    "BandwidthWeighting": "default",
                },
                "Operator": {
                    "Managed": False,
                },
                "InstanceId": "i-00bd",
                "ImageId": "ami-0181",
                "State": {
                    "Code": 16,
                    "Name": "running",
                },
                "PrivateDnsName": "ip-172-31-81-190.ec2.internal",
                "PublicDnsName": "ec2-1-2-3-4.compute-1.amazonaws.com",
                "StateTransitionReason": "",
                "KeyName": "micro-wizard",
                "AmiLaunchIndex": 0,
                "ProductCodes": [],
                "InstanceType": "t2.micro",
                "LaunchTime": datetime.datetime(2024, 12, 21, 7, 28, 24),
                "Placement": {
                    "GroupName": "",
                    "Tenancy": "default",
                    "AvailabilityZone": "us-east-1c",
                },
                "Monitoring": {
                    "State": "disabled",
                },
                "SubnetId": "subnet-0c9",
                "VpcId": "vpc-05b",
                "PrivateIpAddress": "172.31.81.190",
                "PublicIpAddress": "1.2.3.4",
            },
        ],
    }
]
