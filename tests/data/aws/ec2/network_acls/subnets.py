# EC2 Subnet data for use with the Network ACL test

DESCRIBE_SUBNETS_FOR_ACL_TEST = [
    {
        "AvailabilityZoneId": "use1-az1",
        "MapCustomerOwnedIpOnLaunch": False,
        "OwnerId": "000000000000",
        "AssignIpv6AddressOnCreation": False,
        "Ipv6CidrBlockAssociationSet": [],
        "SubnetArn": "arn:aws:ec2:us-east-1:000000000000:subnet/subnet-0a1a",
        "EnableDns64": False,
        "Ipv6Native": False,
        "PrivateDnsNameOptionsOnLaunch": {
            "HostnameType": "ip-name",
            "EnableResourceNameDnsARecord": False,
            "EnableResourceNameDnsAAAARecord": False
        },
        "SubnetId": "subnet-0a1a",
        "State": "available",
        "VpcId": "vpc-0767",
        "CidrBlock": "10.190.1.0/24",
        "AvailableIpAddressCount": 250,
        "AvailabilityZone": "us-east-1b",
        "DefaultForAz": False,
        "MapPublicIpOnLaunch": False
    },
    {
        "AvailabilityZoneId": "use1-az4",
        "MapCustomerOwnedIpOnLaunch": False,
        "OwnerId": "000000000000",
        "AssignIpv6AddressOnCreation": False,
        "Ipv6CidrBlockAssociationSet": [],
        "SubnetArn": "arn:aws:ec2:us-east-1:000000000000:subnet/subnet-06ba",
        "EnableDns64": False,
        "Ipv6Native": False,
        "PrivateDnsNameOptionsOnLaunch": {
            "HostnameType": "ip-name",
            "EnableResourceNameDnsARecord": False,
            "EnableResourceNameDnsAAAARecord": False
        },
        "SubnetId": "subnet-06ba",
        "State": "available",
        "VpcId": "vpc-0767",
        "CidrBlock": "10.190.0.0/24",
        "AvailableIpAddressCount": 251,
        "AvailabilityZone": "us-east-1a",
        "DefaultForAz": False,
        "MapPublicIpOnLaunch": False
    },
]
