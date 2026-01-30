DESCRIBE_NETWORK_ACLS = [
    {
        "Associations": [
            {
                "NetworkAclAssociationId": "aclassoc-080e",
                "NetworkAclId": "acl-077e",
                "SubnetId": "subnet-0fbc",
            },
            {
                "NetworkAclAssociationId": "aclassoc-0c41",
                "NetworkAclId": "acl-077e",
                "SubnetId": "subnet-0a1a",
            },
            {
                "NetworkAclAssociationId": "aclassoc-0d84",
                "NetworkAclId": "acl-077e",
                "SubnetId": "subnet-06ba",
            },
        ],
        "Entries": [
            {
                "CidrBlock": "0.0.0.0/0",
                "Egress": True,
                "Protocol": "-1",
                "RuleAction": "allow",
                "RuleNumber": 100,
            },
            {
                "CidrBlock": "0.0.0.0/0",
                "Egress": True,
                "Protocol": "-1",
                "RuleAction": "deny",
                "RuleNumber": 32767,
            },
            {
                "CidrBlock": "0.0.0.0/0",
                "Egress": False,
                "Protocol": "-1",
                "RuleAction": "allow",
                "RuleNumber": 100,
            },
            {
                "CidrBlock": "0.0.0.0/0",
                "Egress": False,
                "Protocol": "-1",
                "RuleAction": "deny",
                "RuleNumber": 32767,
            },
            {
                "Ipv6CidrBlock": "2001:db8:1234:1a00::/64",
                "Egress": True,
                "Protocol": "-1",
                "RuleAction": "allow",
                "RuleNumber": 100,
            },
        ],
        "IsDefault": True,
        "NetworkAclId": "acl-077e",
        "Tags": [],
        "VpcId": "vpc-0767",
        "OwnerId": "000000000000",
    },
]
