NS_RECORD = {
    "Name": "testdomain.net.",
    "Type": "NS",
    "TTL": 172800,
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
    "AliasTarget": {
        "HostedZoneId": "FAKEZONEID",
        "DNSName": "fakeelb.elb.us-east-1.amazonaws.com.",
        "EvaluateTargetHealth": False,
    },
}

AAAA_RECORD = {
    "Name": "ipv6.example.com.",
    "Type": "AAAA",
    "TTL": 300,
    "ResourceRecords": [
        {"Value": "2001:db8::1"},
        {"Value": "2001:db8::2"},
    ],
}

AAAA_ALIAS_RECORD = {
    "Name": "aliasv6.example.com.",
    "Type": "AAAA",
    "TTL": 60,
    "AliasTarget": {
        "HostedZoneId": "HOSTED_ZONE_2",
        "DNSName": "target-ipv6.example.com.",
        "EvaluateTargetHealth": False,
    },
}

ZONE_RECORDS = [
    {
        "Id": "/hostedzone/FAKEZONEID1",
        "Name": "test.com.",
        "CallerReference": "BD057866-DA11-69AA-AE7C-339CDB669D49",
        "Config": {
            "PrivateZone": False,
        },
        "ResourceRecordSetCount": 8,
    },
    {
        "Id": "/hostedzone/FAKEZONEID2",
        "Name": "test.com.",
        "CallerReference": "BD057866-DA11-69AA-AE7C-339CDB669D49",
        "Config": {
            "PrivateZone": False,
        },
        "ResourceRecordSetCount": 8,
    },
]

GET_ZONES_SAMPLE_RESPONSE = [
    (
        {
            "CallerReference": "044a41db-b8e1-45f8-9962-91c95a123456",
            "Config": {
                "PrivateZone": False,
            },
            "Id": "/hostedzone/HOSTED_ZONE",
            "Name": "example.com.",
            "ResourceRecordSetCount": 7,
        },
        [
            {
                "Name": "example.com.",
                "ResourceRecords": [
                    {
                        "Value": "1.2.3.4",
                    },
                ],
                "TTL": 300,
                "Type": "A",
            },
            {
                "Name": "ipv6.example.com.",
                "ResourceRecords": [
                    {"Value": "2001:db8::1"},
                    {"Value": "2001:db8::2"},
                ],
                "TTL": 300,
                "Type": "AAAA",
            },
            {
                "Name": "example.com.",
                "ResourceRecords": [
                    {
                        "Value": "ec2-1-2-3-4.us-east-2.compute.amazonaws.com",
                    },
                ],
                "TTL": 60,
                "Type": "NS",
            },
            {
                "Name": "example.com.",
                "ResourceRecords": [
                    {
                        "Value": "ns-1234.awsdns-21.co.uk. "
                        "awsdns-hostmaster.amazon.com. 1 1234",
                    },
                ],
                "TTL": 900,
                "Type": "SOA",
            },
            {
                "Name": "_b6e76e6a1b6853211abcdef123454.example.com.",
                "ResourceRecords": [
                    {
                        "Value": "_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws.",
                    },
                ],
                "TTL": 300,
                "Type": "CNAME",
            },
            {
                "Name": "elbv2.example.com.",
                "AliasTarget": {
                    "HostedZoneId": "HOSTED_ZONE_2",
                    "DNSName": "myawesomeloadbalancer.amazonaws.com.",
                    "EvaluateTargetHealth": False,
                },
                "TTL": 60,
                "Type": "A",
            },
            {
                "Name": "aliasv6.example.com.",
                "AliasTarget": {
                    "HostedZoneId": "HOSTED_ZONE_2",
                    "DNSName": "target-ipv6.example.com.",
                    "EvaluateTargetHealth": False,
                },
                "TTL": 60,
                "Type": "AAAA",
            },
            {
                "AliasTarget": {
                    "DNSName": "hello.what.example.com",
                    "EvaluateTargetHealth": False,
                    "HostedZoneId": "HOSTED_ZONE_2",
                },
                "Name": "www.example.com.",
                "Type": "CNAME",
            },
            # Add DNS records that will be pointed to by other DNS records
            {
                "Name": "_1f9ee9f5c4304947879ee77d0a995cc9.something.something.aws.",
                "ResourceRecords": [
                    {
                        "Value": "5.6.7.8",
                    },
                ],
                "TTL": 300,
                "Type": "A",
            },
            {
                "Name": "hello.what.example.com.",
                "ResourceRecords": [
                    {
                        "Value": "9.10.11.12",
                    },
                ],
                "TTL": 300,
                "Type": "A",
            },
        ],
    ),
]

ELASTIC_IP_RELATIONSHIP_TEST_RECORDS = [
    (
        {
            "CallerReference": "test-ref-123",
            "Config": {
                "PrivateZone": False,
            },
            "Id": "/hostedzone/TESTZONE",
            "Name": "test.example.com.",
            "ResourceRecordSetCount": 1,
        },
        [
            {
                "Name": "hello.what.example.com.",
                "ResourceRecords": [
                    {
                        "Value": "192.168.1.1",
                    },
                ],
                "TTL": 300,
                "Type": "A",
            },
        ],
    ),
]

GET_ZONES_WITH_SUBZONE = [
    (
        {
            "Id": "/hostedzone/PARENT_ZONE",
            "Name": "example.com.",
            "ResourceRecordSetCount": 2,
            "Config": {"PrivateZone": False},
        },
        [
            {
                "Name": "example.com.",
                "Type": "A",
                "ResourceRecords": [{"Value": "1.2.3.4"}],
            },
            # This is the crucial delegation record in the parent zone
            {
                "Name": "sub.example.com.",
                "Type": "NS",
                "ResourceRecords": [{"Value": "ns-of-the-subzone.com."}],
            },
        ],
    ),
    (
        {
            "Id": "/hostedzone/SUB_ZONE",
            "Name": "sub.example.com.",
            "ResourceRecordSetCount": 2,
            "Config": {"PrivateZone": False},
        },
        [
            {
                "Name": "sub.example.com.",
                "Type": "NS",
                "ResourceRecords": [{"Value": "ns-of-the-subzone.com."}],
            },
            {
                "Name": "test.sub.example.com.",
                "Type": "A",
                "ResourceRecords": [{"Value": "5.6.7.8"}],
            },
        ],
    ),
]

GET_ZONES_FOR_CYCLE_TEST = [
    (
        # The Parent Zone
        {
            "Id": "/hostedzone/PARENT_ZONE",
            "Name": "example.com.",
            "ResourceRecordSetCount": 1,
            "Config": {"PrivateZone": False},
        },
        [
            # This NS record correctly delegates the subzone
            {
                "Name": "sub.example.com.",
                "Type": "NS",
                "ResourceRecords": [{"Value": "ns.shared-nameserver.com."}],
            },
        ],
    ),
    (
        # The valid Subzone
        {
            "Id": "/hostedzone/SUB_ZONE",
            "Name": "sub.example.com.",
            "ResourceRecordSetCount": 1,
            "Config": {"PrivateZone": False},
        },
        [
            # The subzone's own NS record, pointing to the shared nameserver
            {
                "Name": "sub.example.com.",
                "Type": "NS",
                "ResourceRecords": [{"Value": "ns.shared-nameserver.com."}],
            },
        ],
    ),
    (
        # The unrelated Zone that would have caused the bug
        {
            "Id": "/hostedzone/UNRELATED_ZONE",
            "Name": "unrelated.io.",
            "ResourceRecordSetCount": 1,
            "Config": {"PrivateZone": False},
        },
        [
            # This zone ALSO uses the same nameserver
            {
                "Name": "unrelated.io.",
                "Type": "NS",
                "ResourceRecords": [{"Value": "ns.shared-nameserver.com."}],
            },
        ],
    ),
]
