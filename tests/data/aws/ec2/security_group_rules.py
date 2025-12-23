TEST_REGION = "us-east-1"
TEST_ACCOUNT = "000000000000"

DESCRIBE_SECURITY_GROUP_RULES = {
    "sg-028e2522c72719996": [
        {
            "SecurityGroupRuleId": "sgr-0123456789abcdef0",
            "GroupId": "sg-028e2522c72719996",
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80,
            "CidrIpv4": "203.0.113.0/24",
            "IsEgress": False,
            "SecurityGroupRuleArn": f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT}:security-group-rule/sgr-0123456789abcdef0"
        },
        {
            "SecurityGroupRuleId": "sgr-0123456789abcdef1",
            "GroupId": "sg-028e2522c72719996",
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "CidrIpv4": "203.0.113.0/24",
            "IsEgress": False,
            "SecurityGroupRuleArn": f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT}:security-group-rule/sgr-0123456789abcdef1"
        },
        {
            "SecurityGroupRuleId": "sgr-0123456789abcdef2",
            "GroupId": "sg-028e2522c72719996",
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80,
            "CidrIpv4": "0.0.0.0/0",
            "IsEgress": True,
            "SecurityGroupRuleArn": f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT}:security-group-rule/sgr-0123456789abcdef2"
        },
        {
            "SecurityGroupRuleId": "sgr-0123456789abcdef3",
            "GroupId": "sg-028e2522c72719996",
            "IpProtocol": "-1",
            "CidrIpv4": "0.0.0.0/0",
            "IsEgress": True,
            "SecurityGroupRuleArn": f"arn:aws:ec2:{TEST_REGION}:{TEST_ACCOUNT}:security-group-rule/sgr-0123456789abcdef3"
        }
    ]
}
