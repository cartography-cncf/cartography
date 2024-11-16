# EC2 instance data for use with the Network ACL test
import datetime
from datetime import timezone as tz

INSTANCES_FOR_ACL_TEST = [{
    "ReservationId": "r-03",
    "OwnerId": "000000000000",
    "Groups": [],
    "Instances": [
        {
            "Architecture": "x86_64",
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "AttachTime": "2023-08-04 22:31:02+00:00",
                        "DeleteOnTermination": True,
                        "Status": "attached",
                        "VolumeId": "vol-0e4",
                    },
                },
            ],
            "ClientToken": "b20f8",
            "EbsOptimized": True,
            "EnaSupport": True,
            "Hypervisor": "xen",
            "NetworkInterfaces": [
                {
                    "Attachment": {
                        "AttachTime": "2023-08-04 22:31:01+00:00",
                        "AttachmentId": "eni-attach-0f76",
                        "DeleteOnTermination": True,
                        "DeviceIndex": 0,
                        "Status": "attached",
                        "NetworkCardIndex": 0,
                    },
                    "Description": "",
                    "Groups": [
                        {
                            "GroupId": "sg-0564",
                            "GroupName": "group-name-1",
                        },
                    ],
                    "Ipv6Addresses": [],
                    "MacAddress": "11:22:33:44:55:66",
                    "NetworkInterfaceId": "eni-0430",
                    "OwnerId": "000000000000",
                    "PrivateIpAddress": "10.190.1.148",
                    "PrivateIpAddresses": [
                        {
                            "Primary": True,
                            "PrivateIpAddress": "10.190.1.148",
                        },
                    ],
                    "SourceDestCheck": True,
                    "Status": "in-use",
                    "SubnetId": "subnet-0a1a",
                    "VpcId": "vpc-0767",
                    "InterfaceType": "interface",
                },
            ],
            "RootDeviceName": "/dev/xvda",
            "RootDeviceType": "ebs",
            "SecurityGroups": [
                {
                    "GroupId": "sg-0564",
                    "GroupName": "group-name-1",
                },
            ],
            "SourceDestCheck": True,
            "Tags": [
                {
                    "Key": "Name",
                    "Value": "prod-tag",
                },
            ],
            "VirtualizationType": "hvm",
            "CpuOptions": {
                "CoreCount": 1,
                "ThreadsPerCore": 2,
            },
            "CapacityReservationSpecification": {
                "CapacityReservationPreference": "open",
            },
            "HibernationOptions": {
                "Configured": False,
            },
            "MetadataOptions": {
                "State": "applied",
                "HttpTokens": "optional",
                "HttpPutResponseHopLimit": 1,
                "HttpEndpoint": "enabled",
                "HttpProtocolIpv6": "disabled",
                "InstanceMetadataTags": "disabled",
            },
            "EnclaveOptions": {
                "Enabled": False,
            },
            "PlatformDetails": "Linux/UNIX",
            "UsageOperation": "RunInstances",
            "UsageOperationUpdateTime": "2023-08-04 22:31:01+00:00",
            "PrivateDnsNameOptions": {
                "HostnameType": "ip-name",
                "EnableResourceNameDnsARecord": False,
                "EnableResourceNameDnsAAAARecord": False,
            },
            "MaintenanceOptions": {
                "AutoRecovery": "default",
            },
            "CurrentInstanceBootMode": "legacy-bios",
            "InstanceId": "i-0ba7",
            "ImageId": "ami-0414",
            "State": {
                "Code": 16,
                "Name": "running",
            },
            "PrivateDnsName": "ip-10-190-1-148.ec2.internal",
            "PublicDnsName": "",
            "StateTransitionReason": "",
            "AmiLaunchIndex": 0,
            "ProductCodes": [],
            "InstanceType": "t3.micro",
            "LaunchTime": datetime.datetime(2023, 8, 4, 22, 31, 1, tzinfo=tz.utc),
            "Placement": {
                "GroupName": "",
                "Tenancy": "default",
                "AvailabilityZone": "us-east-1b",
            },
            "Monitoring": {
                "State": "disabled",
            },
            "SubnetId": "subnet-0a1a",
            "VpcId": "vpc-0767",
            "PrivateIpAddress": "10.190.1.148",
        },
    ],
}]
