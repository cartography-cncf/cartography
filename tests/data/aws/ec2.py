DESCRIBE_KEY_PAIRS = {
    "KeyPairs": [
        {
            "KeyFingerprint": "11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11:11",
            "KeyName": "sample_key_pair_1",
        },
        {
            "KeyFingerprint": "22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22:22",
            "KeyName": "sample_key_pair_2",
        },
        {
            "KeyFingerprint": "33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33:33",
            "KeyName": "sample_key_pair_3",
        },
    ],
}

DESCRIBE_TAGS = {
    "Tags": [
        {
            "ResourceType": "instance",
            "ResourceId": "tagged-instance",
            "Value": "foo",
            "Key": "Name",
        },
        {
            "ResourceType": "network-interface",
            "ResourceId": "tagged-network-interface",
            "Value": "bar",
            "Key": "Name",
        },
        {
            "ResourceType": "security-group",
            "ResourceId": "tagged-security-group",
            "Value": "High",
            "Key": "Importance",
        },
        {
            "ResourceType": "subnet",
            "ResourceId": "tagged-subnet",
            "Value": "Test",
            "Key": "Environment",
        },
        {
            "ResourceType": "vpc",
            "ResourceId": "tagged-vpc",
            "Value": "Private",
            "Key": "Name",
        },
    ],
}

TARGET_GROUPS = [
    {
        'TargetType': 'instance',
        'Targets': ["i-0f76fade"],
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
        'ListenerArn': "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/app/myawesomeloadb/LBId/ListId",
        'Port': 443,
        'Protocol': 'HTTPS',
        'TargetGroupArn': 'arn:aws:ec2:us-east-1:012345678912:targetgroup',
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
        'DNSName': 'myawesomeloadbalancer.amazonaws.com',
        'CreatedTime': '10-27-2019 12:35AM',
        'LoadBalancerName': 'myawesomeloadbalancer',
        'Type': 'application',
        'Scheme': 'internet-facing',
        'AvailabilityZones': [
            {
                'ZoneName': 'myAZ',
                'SubnetId': 'mysubnetIdA',
                'LoadBalancerAddresses': [
                    {
                        'IpAddress': '50.0.1.0',
                        'AllocationId': 'someId',
                    },
                ],
            },
        ],
        'SecurityGroups': ['sg-123456', 'sg-234567'],
        'Listeners': LOAD_BALANCER_LISTENERS,
        'TargetGroups': TARGET_GROUPS,
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
