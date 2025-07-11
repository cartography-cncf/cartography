DESCRIBE_SECURITY_GROUP_RULES = [
    {
        "SecurityGroupRuleId": "sgr-01234567890abcdef",
        "GroupId": "sg-028e2522c72719996",
        "IsEgress": False,
        "IpProtocol": "tcp",
        "FromPort": 80,
        "ToPort": 80,
        "CidrIpv4": "203.0.113.0/24"
    },
    {
        "SecurityGroupRuleId": "sgr-abcdef01234567890",
        "GroupId": "sg-028e2522c72719996",
        "IsEgress": False,
        "IpProtocol": "tcp",
        "FromPort": 443,
        "ToPort": 443,
        "CidrIpv4": "203.0.113.0/24"
    },
    {
        "SecurityGroupRuleId": "sgr-11111111111111111",
        "GroupId": "sg-028e2522c72719996",
        "IsEgress": True,
        "IpProtocol": "tcp",
        "FromPort": 80,
        "ToPort": 80,
        "CidrIpv4": "0.0.0.0/0"
    },
    {
        "SecurityGroupRuleId": "sgr-22222222222222222",
        "GroupId": "sg-028e2522c72719996",
        "IsEgress": True,
        "IpProtocol": "-1",
        "CidrIpv4": "8.8.8.8/32"
    },
    {
        "SecurityGroupRuleId": "sgr-33333333333333333",
        "GroupId": "sg-028e2522c72719996",
        "IsEgress": True,
        "IpProtocol": "tcp",
        "FromPort": 443,
        "ToPort": 443,
        "CidrIpv4": "0.0.0.0/0"
    }
]
