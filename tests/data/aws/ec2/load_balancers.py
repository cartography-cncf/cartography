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
        'Rules': [
            {
                'ConditionStrings': {
                    "path_pattern": "foo",
                },
                'RuleArn': 'arn:aws:elasticloadbalancing:us-east-1:000000000000:listener-rule/app/myawesomeloadb/' +
                           '50dc6c495c0c9188/f2f7dc8efc522ab2/9683b2d02a6cabee',
                'Actions': [
                    {
                        'id': 'arn:aws:elasticloadbalancing:us-east-1:000000000000:listener-rule/app/myawesomeloadb/' +
                              '50dc6c495c0c9188/f2f7dc8efc522ab2/9683b2d02a6cabee-action-default',
                        'Type': 'forward',
                        'ForwardConfig': {
                            'TargetGroups': [],
                        },
                    },
                ],
            },
        ],
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
        'LoadBalancerArn': 'arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/' +
                           'amyawesomeloadbalancer/50dc6c495c0c9188',
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
