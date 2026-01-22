import datetime

GET_LOAD_BALANCER_V2_DATA = [
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890123456",
        "DNSName": "test-alb-1234567890.us-east-1.elb.amazonaws.com",
        "CanonicalHostedZoneId": "Z35SXDOTRQ7X7K",
        "CreatedTime": datetime.datetime(2021, 1, 1, 12, 0, 0),
        "LoadBalancerName": "test-alb",
        "Scheme": "internet-facing",
        "VpcId": "vpc-12345678",
        "State": {"Code": "active"},
        "Type": "application",
        "AvailabilityZones": [
            {
                "ZoneName": "us-east-1a",
                "SubnetId": "subnet-11111111",
            },
            {
                "ZoneName": "us-east-1b",
                "SubnetId": "subnet-22222222",
            },
        ],
        "SecurityGroups": ["sg-12345678", "sg-87654321"],
        "IpAddressType": "ipv4",
        "Listeners": [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890123456/abcdef1234567890",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890123456",
                "Port": 443,
                "Protocol": "HTTPS",
                "SslPolicy": "ELBSecurityPolicy-2016-08",
            },
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/test-alb/1234567890123456/1234567890abcdef",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/app/test-alb/1234567890123456",
                "Port": 80,
                "Protocol": "HTTP",
            },
        ],
        "TargetGroups": [
            {
                "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:targetgroup/test-tg/1234567890123456",
                "TargetGroupName": "test-tg",
                "Protocol": "HTTP",
                "Port": 80,
                "TargetType": "instance",
                "Targets": ["i-1234567890abcdef0", "i-0987654321fedcba0"],
            },
        ],
    },
    {
        "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/net/test-nlb/abcdef0123456789",
        "DNSName": "test-nlb-abcdef0123.us-east-1.elb.amazonaws.com",
        "CanonicalHostedZoneId": "Z26RNL4JYFTOTI",
        "CreatedTime": datetime.datetime(2021, 6, 15, 9, 30, 0),
        "LoadBalancerName": "test-nlb",
        "Scheme": "internal",
        "VpcId": "vpc-12345678",
        "State": {"Code": "active"},
        "Type": "network",
        "AvailabilityZones": [
            {
                "ZoneName": "us-east-1a",
                "SubnetId": "subnet-33333333",
            },
        ],
        # NLBs don't have security groups
        "IpAddressType": "ipv4",
        "Listeners": [
            {
                "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/net/test-nlb/abcdef0123456789/fedcba9876543210",
                "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:loadbalancer/net/test-nlb/abcdef0123456789",
                "Port": 443,
                "Protocol": "TLS",
            },
        ],
        "TargetGroups": [],
    },
]
