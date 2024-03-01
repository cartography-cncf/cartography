NS_RECORD = {
    "Name": "testdomain.net.",
    "Type": "NS",
    "TTL": 172800,
    "arn": "arn-123",
    "consolelink": 'www.dff.com',
    "ResourceRecords": [
        {
            "Value": "ns-856.awsdns-43.net",
        },
        {
            "Value": "ns-1418.awsdns-49.org.",
        },
        {
            "Value": "ns-1913.awsdns-47.co.uk.",
        },
        {
            "Value": "ns-192.awsdns-24.com.",
        },
    ],
}

CNAME_RECORD = {
    "Name": "subdomain.lyft.com.",
    "Type": "CNAME",
    "SetIdentifier": "ca",
    "GeoLocation": {
        "CountryCode": "US",
        "SubdivisionCode": "CA",
    },
    "arn": "arn-123",
    "consolelink": 'www.dff.com',
    "AliasTarget": {
        "HostedZoneId": "FAKEZONEID",
        "DNSName": "fakeelb.elb.us-east-1.amazonaws.com.",
        "EvaluateTargetHealth": False,
    },
}

ZONE_RECORDS = [
    {
        "Id": "/hostedzone/FAKEZONEID1",
        "Name": "test.com.",
        'arn': 'arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography',
        'consolelink': 'www.consolelinkdemo.com',
        "CallerReference": "BD057866-DA11-69AA-AE7C-339CDB669D49",
        "Config": {
            "PrivateZone": False,
        },
        "ResourceRecordSetCount": 8,
    },
    {
        "Id": "/hostedzone/FAKEZONEID2",
        "Name": "test.com.",
        'arn': 'arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography',
        'consolelink': 'www.consolelinkdemo.com',
        "CallerReference": "BD057866-DA11-69AA-AE7C-339CDB669D49",
        "Config": {
            "PrivateZone": False,
        },
        "ResourceRecordSetCount": 8,
    },
]

GET_ZONES_SAMPLE_RESPONSE = [(
    {
        'CallerReference': '044a41db-b8e1-45f8-9962-91c95a123456',
        'arn': 'arn:aws:kms:eu-west-1:000000000000:alias/key2-cartography',
        'consolelink': 'www.consolelinkdemo.com',
        'Config': {
            'PrivateZone': False,
        },
        'Id': '/hostedzone/HOSTED_ZONE',
        'Name': 'example.com.',
        "arn": "arn-123",
        "consolelink": 'www.dff.com',
        'ResourceRecordSetCount': 5,
    }, [
        {
            'Name': 'example.com.',

            'ResourceRecords': [{
                'Value': '1.2.3.4',
            }],
            'TTL': 300,
            "arn": "arn-123",
            "consolelink": 'www.dff.com',
            'Type': 'A',
        }, {
            'Name': 'example.com.',
            'ResourceRecords': [{
                'Value': 'ec2-1-2-3-4.us-east-2.compute.amazonaws.com',
            }],
            'TTL': 60,
            "arn": "arn-123",
            'Type': 'NS',
            "consolelink": 'www.dff.com',
        }, {
            'Name': 'example.com.',
            'ResourceRecords': [{
                'Value': 'ns-1234.awsdns-21.co.uk. '
                         'awsdns-hostmaster.amazon.com. 1 1234',
            }],
            'TTL': 900,
            "arn": "arn-123",
            'Type': 'SOA',
        }, {
            'Name': '_b6e76e6a1b6853211abcdef123454.example.com.',
            'ResourceRecords': [{
                'Value': '_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws.',
            }],
            'TTL': 300,
            "arn": "arn-123",
            'Type': 'CNAME',
            "consolelink": 'www.dff.com',

        }, {
            'Name': 'elbv2.example.com.',
            'AliasTarget': {
                'HostedZoneId': 'HOSTED_ZONE_2',
                'DNSName': 'myawesomeloadbalancer.amazonaws.com.',
                'EvaluateTargetHealth': False,
                "arn": "arn-123",
            },
            'TTL': 60,
            'Type': 'A',
            "arn": "arn-123",
            "consolelink": 'www.dff.com',
        }, {
            'AliasTarget': {
                'DNSName': 'hello.what.example.com',
                'EvaluateTargetHealth': False,
                'HostedZoneId': 'HOSTED_ZONE_2',
            },
            'Name': 'www.example.com.',
            'Type': 'CNAME',
            "arn": "arn-123",
            "consolelink": 'www.dff.com',
        },
    ],
)]
