ALB_ID = "myawesomeloadbalancer.amazonaws.com"
APIGW_ID = "'arn:aws:apigateway:us-east-1::/restapis/test-001/stages/Cartography-testing-infra'"
LIST_WEB_ACL = [
    {
        'ARN': 'arn:aws:wafv2:us-east-1:000000000000:regional/webacl/waf_test/9a1ad414-6e3b-47ce-8366-6b8f26ba467d',
        'Capacity': 525,
        'DefaultAction': {
            'Allow': {}
        },
        'Description': '',
        'Id': '9a1ad414-6e3b-47ce-8366-6b8f26ba467d',
        'LabelNamespace': 'awswaf:000000000000:webacl:waf_test:',
        'ManagedByFirewallManager': False,
        'Name': 'waf_test',
        'Resources': {
            'ALBs': [ALB_ID],
            'APIGWs': [APIGW_ID],
        },
        'Rules': [
            {
                'Name': 'AWS-AWSManagedRulesAmazonIpReputationList',
                'OverrideAction': {
                    'None': {}
                },
                'Priority': 0,
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'Name': 'AWSManagedRulesAmazonIpReputationList',
                        'VendorName': 'AWS'
                    }
                },
                'VisibilityConfig': {
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'AWS-AWSManagedRulesAmazonIpReputationList',
                    'SampledRequestsEnabled': True
                }
            },
            {
                'Name': 'AWS-AWSManagedRulesSQLiRuleSet',
                'OverrideAction': {
                    'None': {}
                },
                'Priority': 1,
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'Name': 'AWSManagedRulesSQLiRuleSet',
                        'VendorName': 'AWS'
                    }
                },
                'VisibilityConfig': {
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'AWS-AWSManagedRulesSQLiRuleSet',
                    'SampledRequestsEnabled': True
                }
            },
            {
                'Name': 'AWS-AWSManagedRulesUnixRuleSet',
                'OverrideAction': {
                    'None': {}
                },
                'Priority': 2,
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'Name': 'AWSManagedRulesUnixRuleSet',
                        'VendorName': 'AWS'
                    }
                },
                'VisibilityConfig': {
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'AWS-AWSManagedRulesUnixRuleSet',
                    'SampledRequestsEnabled': True
                }
            },
            {
                'Name': 'AWS-AWSManagedRulesLinuxRuleSet',
                'OverrideAction': {
                    'None': {}
                },
                'Priority': 3,
                'Statement': {
                    'ManagedRuleGroupStatement': {
                        'Name': 'AWSManagedRulesLinuxRuleSet',
                        'VendorName': 'AWS'
                    }
                },
                'VisibilityConfig': {
                    'CloudWatchMetricsEnabled': True,
                    'MetricName': 'AWS-AWSManagedRulesLinuxRuleSet',
                    'SampledRequestsEnabled': True
                }
            }
        ],
        'VisibilityConfig': {
            'CloudWatchMetricsEnabled': True,
            'MetricName': 'waf_test',
            'SampledRequestsEnabled': True
        }
    }
]
