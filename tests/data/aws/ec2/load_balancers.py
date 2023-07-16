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
    {
        'ListenerArn': "arn:aws:elasticloadbalancing:us-east-1:000000000000:listener/gwy/mytestgwy/gwyLBId/gwyListId",
        'Port': 500,
        'Protocol': 'GENEVE',
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
        'LoadBalancerArn': (
            "arn:aws:ec2:elasticloadbalancing:us-east-1:000000000000:"
            "loadbalancer/app/myawesomeloadbalancer/someid"
        ),
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
    {
        'LoadBalancerArn': (
            'arn:aws:elasticloadbalancing:eu-north-1:167992319538'
            ':loadbalancer/gwy/test-gateway-load-balancer/180ff0c1e66f6754'
        ),
        'CreatedTime': '2023-07-14 17:27:50.495000+00:00',
        'LoadBalancerName': 'test-gateway-load-balancer',
        'VpcId': 'vpc-03e880ef713e1f725',
        'State': {
            'Code': 'active',
        },
        'Type': 'gateway',
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
        'IpAddressType': 'ipv4',
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
