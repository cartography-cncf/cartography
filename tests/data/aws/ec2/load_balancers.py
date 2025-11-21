TARGET_GROUPS = [
    {
        "TargetType": "instance",
        "Targets": ["i-0f76fade"],
    },
]

# 'TargetGroups': [
#         'TargetGroupArn': 'string',
#         ...
#         'TargetType': 'instance'|'ip'|'lambda',
#         'Targets': ["i-0f76fade"]
#     ]

LOAD_BALANCER_LISTENERS = [
    {
        "ListenerArn": "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/myawesomeloadb/LBId/ListId",
        "Port": 443,
        "Protocol": "HTTPS",
        "TargetGroupArn": "arn:aws:ec2:us-east-1:012345678912:targetgroup",
    },
]

# Listener fields
# 'Listeners': [
#     {
#         'ListenerArn': 'string',
#         'LoadBalancerArn': 'string',
#         'Port': 123,
#         'Protocol': 'HTTP''HTTPS''TCP''TLS''UDP''TCP_UDP',
#         'Certificates': [
#             {
#                 'CertificateArn': 'string',
#                 'IsDefault': TrueFalse
#             },
#         ],
#         'SslPolicy': 'string',
#         'DefaultActions': [
#             {
#                 'Type': 'forward''authenticate-oidc''authenticate-cognito''redirect''fixed-response',
#                 'TargetGroupArn': 'string', # Used with forward
#                 'AuthenticateOidcConfig': {
#                     'Issuer': 'string',
#                     'AuthorizationEndpoint': 'string',
#                     'TokenEndpoint': 'string',
#                     'UserInfoEndpoint': 'string',
#                     'ClientId': 'string',
#                     'ClientSecret': 'string',
#                     'SessionCookieName': 'string',
#                     'Scope': 'string',
#                     'SessionTimeout': 123,
#                     'AuthenticationRequestExtraParams': {
#                         'string': 'string'
#                     },
#                     'OnUnauthenticatedRequest': 'deny''allow''authenticate',
#                     'UseExistingClientSecret': TrueFalse
#                 },
#                 'AuthenticateCognitoConfig': {
#                     'UserPoolArn': 'string',
#                     'UserPoolClientId': 'string',
#                     'UserPoolDomain': 'string',
#                     'SessionCookieName': 'string',
#                     'Scope': 'string',
#                     'SessionTimeout': 123,
#                     'AuthenticationRequestExtraParams': {
#                         'string': 'string'
#                     },
#                     'OnUnauthenticatedRequest': 'deny''allow''authenticate'
#                 },
#                 'Order': 123,
#                 'RedirectConfig': {
#                     'Protocol': 'string',
#                     'Port': 'string',
#                     'Host': 'string',
#                     'Path': 'string',
#                     'Query': 'string',
#                     'StatusCode': 'HTTP_301''HTTP_302'
#                 },
#                 'FixedResponseConfig': {
#                     'MessageBody': 'string',
#                     'StatusCode': 'string',
#                     'ContentType': 'string'
#                 }
#             },
#         ]
#     },
# ],

LOAD_BALANCER_DATA = [
    {
        "DNSName": "myawesomeloadbalancer.amazonaws.com",
        "CreatedTime": "10-27-2019 12:35AM",
        "LoadBalancerName": "myawesomeloadbalancer",
        "Type": "application",
        "Scheme": "internet-facing",
        "AvailabilityZones": [
            {
                "ZoneName": "myAZ",
                "SubnetId": "mysubnetIdA",
                "LoadBalancerAddresses": [
                    {
                        "IpAddress": "50.0.1.0",
                        "AllocationId": "someId",
                    },
                ],
            },
        ],
        "SecurityGroups": ["sg-123456", "sg-234567"],
        "Listeners": LOAD_BALANCER_LISTENERS,
        "TargetGroups": TARGET_GROUPS,
    },
    # Entry with missing DNSName to test skip/warning logic
    {
        "CreatedTime": "10-27-2019 12:35AM",
        "LoadBalancerName": "missingdnsnamelb",
        "Type": "application",
        "Scheme": "internet-facing",
        "AvailabilityZones": [
            {
                "ZoneName": "myAZ",
                "SubnetId": "mysubnetIdB",
                "LoadBalancerAddresses": [
                    {
                        "IpAddress": "50.0.2.0",
                        "AllocationId": "someId2",
                    },
                ],
            },
        ],
        "SecurityGroups": ["sg-345678"],
        "Listeners": LOAD_BALANCER_LISTENERS,
        "TargetGroups": TARGET_GROUPS,
    },
]

# 'LoadBalancers': [
#     {
#         'LoadBalancerArn': 'string',
#         'DNSName': 'string',
#         'CanonicalHostedZoneId': 'string',
#         'CreatedTime': datetime(2015, 1, 1),
#         'LoadBalancerName': 'string',
#         'Scheme': 'internet-facing''internal',
#         'VpcId': 'string',
#         'State': {
#             'Code': 'active''provisioning''active_impaired''failed',
#             'Reason': 'string'
#         },
#         'Type': 'application''network',
#         'AvailabilityZones': [
#             {
#                 'ZoneName': 'string',
#                 'SubnetId': 'string',
#                 'LoadBalancerAddresses': [
#                     {
#                         'IpAddress': 'string',
#                         'AllocationId': 'string'
#                     },
#                 ]
#             },
#         ],
#         'SecurityGroups': [
#             'string',
#         ],
#         'IpAddressType': 'ipv4''dualstack'
#         'Listeners': [
#             {
#                 'ListenerArn': 'string',
#                 'LoadBalancerArn': 'string',
#                 'Port': 123,
#                 'Protocol': 'HTTP'|'HTTPS'|'TCP'|'TLS'|'UDP'|'TCP_UDP',
#                 'Certificates': [
#                     {
#                         'CertificateArn': 'string',
#                         'IsDefault': True|False
#                     },
#                 ],
#                 'SslPolicy': 'string',
#                 'DefaultActions': [
#                     {
#                         "TargetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:XXXXXXXXXXXX:targetgroup/Y",
#                         "Type": "forward"
#                     }
#                 ]
#             }
#         ],
#         'TargetGroups': [
#             'TargetGroupArn': 'string',
#             ...
#             'TargetType': 'instance'|'ip'|'lambda',
#             'Targets': ["i-0f76fade"]
#         ]
#     },
# ],

DESCRIBE_LOAD_BALANCERS = {
    "LoadBalancerDescriptions": [
        {
            "LoadBalancerName": "test-lb-1",
            "DNSName": "test-lb-1-1234567890.us-east-1.elb.amazonaws.com",
            "CanonicalHostedZoneName": "test-lb-1-1234567890.us-east-1.elb.amazonaws.com",
            "CanonicalHostedZoneNameID": "Z35SXDOTRQ7X7K",
            "Scheme": "internet-facing",
            "CreatedTime": "2024-01-01T00:00:00.000Z",
            "SecurityGroups": ["SOME_GROUP_ID_2", "THIS_IS_A_SG_ID"],
            "Instances": [
                {"InstanceId": "i-01"},
                {"InstanceId": "i-02"},
            ],
            "SourceSecurityGroup": {
                "GroupName": "default",
                "OwnerAlias": "abcdef",
            },
            "ListenerDescriptions": [
                {
                    "Listener": {
                        "LoadBalancerPort": 80,
                        "Protocol": "HTTP",
                        "InstancePort": 8080,
                        "InstanceProtocol": "HTTP",
                    },
                    "PolicyNames": ["test-policy-1"],
                },
                {
                    "Listener": {
                        "LoadBalancerPort": 443,
                        "Protocol": "HTTPS",
                        "InstancePort": 8443,
                        "InstanceProtocol": "HTTPS",
                    },
                    "PolicyNames": ["test-policy-2"],
                },
            ],
        },
        {
            "LoadBalancerName": "test-lb-2",
            "DNSName": "test-lb-2-1234567890.us-east-1.elb.amazonaws.com",
            "CanonicalHostedZoneName": "test-lb-2-1234567890.us-east-1.elb.amazonaws.com",
            "CanonicalHostedZoneNameID": "Z35SXDOTRQ7X7K",
            "Scheme": "internal",
            "CreatedTime": "2024-01-02T00:00:00.000Z",
            "Instances": [
                {"InstanceId": "i-03"},
            ],
            "ListenerDescriptions": [
                {
                    "Listener": {
                        "LoadBalancerPort": 8080,
                        "Protocol": "TCP",
                        "InstancePort": 8080,
                        "InstanceProtocol": "TCP",
                    },
                    "PolicyNames": ["test-policy-3"],
                },
            ],
        },
    ],
}
