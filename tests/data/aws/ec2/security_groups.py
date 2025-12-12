DESCRIBE_SGS = [
    {
        "Description": "security group vpc2-id1",
        "GroupName": "sq-vpc2-id1",
        "IpPermissions": [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "203.0.113.0/24",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 80,
                "UserIdGroupPairs": [],
            },
            {
                "FromPort": 443,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "203.0.113.0/24",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 443,
                "UserIdGroupPairs": [],
            },
        ],
        "OwnerId": "000000000000",
        "GroupId": "sg-028e2522c72719996",
        "IpPermissionsEgress": [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 80,
                "UserIdGroupPairs": [],
            },
            {
                "IpProtocol": "-1",
                "IpRanges": [
                    {
                        "CidrIp": "8.8.8.8/32",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [],
            },
            {
                "FromPort": 443,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 443,
                "UserIdGroupPairs": [],
            },
        ],
        "VpcId": "vpc-05326141848d1c681",
    },
    {
        "Description": "default VPC security group",
        "GroupName": "default",
        "IpPermissions": [
            {
                "IpProtocol": "-1",
                "IpRanges": [],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [
                    {
                        "GroupId": "sg-053dba35430032a0d",
                        "UserId": "000000000000",
                    },
                ],
            },
        ],
        "OwnerId": "000000000000",
        "GroupId": "sg-053dba35430032a0d",
        "IpPermissionsEgress": [
            {
                "IpProtocol": "-1",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [],
            },
        ],
        "VpcId": "vpc-025873e026b9e8ee6",
    },
    {
        "Description": "security group vpc1-id1",
        "GroupName": "sq-vpc1-id1",
        "IpPermissions": [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "203.0.113.0/24",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 80,
                "UserIdGroupPairs": [],
            },
            {
                "FromPort": 443,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "203.0.113.0/24",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 443,
                "UserIdGroupPairs": [],
            },
        ],
        "OwnerId": "000000000000",
        "GroupId": "sg-06c795c66be8937be",
        "IpPermissionsEgress": [
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 80,
                "UserIdGroupPairs": [],
            },
            {
                "IpProtocol": "-1",
                "IpRanges": [
                    {
                        "CidrIp": "8.8.8.8/32",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [],
            },
            {
                "FromPort": 443,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 443,
                "UserIdGroupPairs": [],
            },
        ],
        "VpcId": "vpc-025873e026b9e8ee6",
    },
    {
        "Description": "default VPC security group",
        "GroupName": "default",
        "IpPermissions": [
            {
                "IpProtocol": "-1",
                "IpRanges": [],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [
                    {
                        "GroupId": "sg-0fd4fff275d63600f",
                        "UserId": "000000000000",
                    },
                ],
            },
        ],
        "OwnerId": "000000000000",
        "GroupId": "sg-0fd4fff275d63600f",
        "IpPermissionsEgress": [
            {
                "IpProtocol": "-1",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [],
            },
        ],
        "VpcId": "vpc-05326141848d1c681",
    },
    {
        "Description": "web server security group",
        "GroupName": "web-server-sg",
        "IpPermissions": [
            {
                "FromPort": 22,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "10.0.0.0/8",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 22,
                "UserIdGroupPairs": [
                    {
                        "GroupId": "sg-028e2522c72719996",
                        "UserId": "000000000000",
                    },
                ],
            },
            {
                "FromPort": 80,
                "IpProtocol": "tcp",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "ToPort": 80,
                "UserIdGroupPairs": [],
            },
        ],
        "OwnerId": "000000000000",
        "GroupId": "sg-web-server-12345",
        "IpPermissionsEgress": [
            {
                "IpProtocol": "-1",
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0",
                    },
                ],
                "Ipv6Ranges": [],
                "PrefixListIds": [],
                "UserIdGroupPairs": [],
            },
        ],
        "VpcId": "vpc-05326141848d1c681",
    },
]
