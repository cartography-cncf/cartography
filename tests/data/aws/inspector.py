from datetime import datetime


LIST_FINDINGS_NETWORK = [
    {
        'awsAccountId': '123456789011',
        'description': 'string',
        'findingArn': 'arn:aws:test123',
        'firstObservedAt': datetime(2015, 1, 1),
        'inspectorScore': 123.0,
        'inspectorScoreDetails': {
            'adjustedCvss': {
                'adjustments': [
                    {
                        'metric': 'string',
                        'reason': 'string',
                    },
                ],
                'cvssSource': 'string',
                'score': 123.0,
                'scoreSource': 'string',
                'scoringVector': 'string',
                'version': 'string',
            },
        },
        'lastObservedAt': datetime(2015, 1, 1),
        'networkReachabilityDetails': {
            'networkPath': {
                'steps': [
                    {
                        'componentId': 'string',
                        'componentType': 'string',
                    },
                ],
            },
            'openPortRange': {
                'begin': 123,
                'end': 124,
            },
            'protocol': 'TCP',
        },
        'remediation': {
            'recommendation': {
                'Url': 'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2008-4250',
                'text': 'string',
            },
        },
        'resources': [
            {
                'details': {
                    'awsEc2Instance': {
                        'iamInstanceProfileArn': 'string',
                        'imageId': 'string',
                        'ipV4Addresses': [
                            'string',
                        ],
                        'ipV6Addresses': [
                            'string',
                        ],
                        'keyName': 'string',
                        'launchedAt': datetime(2015, 1, 1),
                        'platform': 'string',
                        'subnetId': 'string',
                        'type': 'string',
                        'vpcId': 'string',
                    },
                    'awsEcrContainerImage': {
                        'architecture': 'string',
                        'author': 'string',
                        'imageHash': 'string',
                        'imageTags': [
                            'string',
                        ],
                        'platform': 'string',
                        'pushedAt': datetime(2015, 1, 1),
                        'registry': 'string',
                        'repositoryName': 'string',
                    },
                },
                'id': 'i-instanceid',
                'partition': 'string',
                'region': 'string',
                'tags': {
                    'string': 'string',
                },
                'type': 'AWS_EC2_INSTANCE',
            },
        ],
        'severity': 'INFORMATIONAL',
        'status': 'ACTIVE',
        'title': 'string',
        'type': 'NETWORK_REACHABILITY',
        'updatedAt': datetime(2015, 1, 1),
    },
]

LIST_FINDINGS_EC2_PACKAGE = [
    {
        'awsAccountId': '123456789012',
        'description': 'The NFSv4 implementation in the Linux kernel through '
        '4.11.1 allows local users to cause a denial of service '
        '(resource consumption) by leveraging improper channel '
        'callback shutdown when unmounting an NFSv4 filesystem, aka '
        'a "module reference and kernel daemon" leak.',
        'findingArn': 'arn:aws:test456',
        'firstObservedAt': datetime(2022, 5, 4, 16, 23, 3, 692000),
        'inspectorScore': 5.5,
        'inspectorScoreDetails': {
            'adjustedCvss': {
                'adjustments': [],
                'cvssSource': 'REDHAT_CVE',
                'score': 5.5,
                'scoreSource': 'REDHAT_CVE',
                'scoringVector': 'CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H',
                'version': '3.0',
            },
        },
        'lastObservedAt': datetime(2022, 5, 4, 16, 23, 3, 692000),
        'packageVulnerabilityDetails': {
            'cvss': [
                {
                    'baseScore': 5.5,
                    'scoringVector': 'CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H',
                    'source': 'REDHAT_CVE',
                    'version': '3.0',
                },
                {
                    'baseScore': 4.9,
                    'scoringVector': 'AV:L/AC:L/Au:N/C:N/I:N/A:C',
                    'source': 'NVD',
                    'version': '2.0',
                },
                {
                    'baseScore': 5.5,
                    'scoringVector': 'CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H',
                    'source': 'NVD',
                    'version': '3.0',
                },
            ],
            'referenceUrls': [],
            'relatedVulnerabilities': [],
            'source': 'REDHAT_CVE',
            'sourceUrl': 'https://access.redhat.com/security/cve/CVE-2017-9059',
            'vendorCreatedAt': datetime(2017, 4, 25, 17, 0),
            'vendorSeverity': 'Moderate',
            'vulnerabilityId': 'CVE-2017-9059',
            'vulnerablePackages': [
                {
                    'arch': 'X86_64',
                    'epoch': 0,
                    'name': 'kernel-tools',
                    'packageManager': 'OS',
                    'release': '6.29.amzn1',
                    'version': '4.9.17',
                },
                {
                    'arch': 'X86_64',
                    'epoch': 0,
                    'name': 'kernel',
                    'packageManager': 'OS',
                    'release': '6.29.amzn1',
                    'version': '4.9.17',
                },
            ],
        },
        'remediation': {'recommendation': {'text': 'None Provided'}},
        'resources': [{
            'details': {
                'awsEc2Instance': {
                    'iamInstanceProfileArn': 'arn:aws:iam::123456789012:instance-profile/InspectorTestingRole',
                    'imageId': 'ami-00700700',
                    'ipV4Addresses': ['10.0.1.3'],
                    'ipV6Addresses': [],
                    'keyName': 'InspectorTest',
                    'launchedAt': datetime(2022, 5, 4, 16, 15, 41),
                    'platform': 'AMAZON_LINUX',
                    'subnetId': 'subnet-11203981029833100',
                    'type': 't2.micro',
                    'vpcId': 'vpc-11203981029822100',
                },
            },
            'id': 'i-88503981029833100',
            'partition': 'aws',
            'region': 'us-west-2',
            'tags': {},
            'type': 'AWS_EC2_INSTANCE',
        }],
        'severity': 'MEDIUM',
        'status': 'ACTIVE',
        'title': 'CVE-2017-9059 - kernel-tools, kernel',
        'type': 'PACKAGE_VULNERABILITY',
        'updatedAt': datetime(2022, 5, 4, 16, 23, 3, 692000),
    },
    {
        'awsAccountId': '123456789011',
        'description': 'A buffer overflow vulnerability in OpenSSL allows remote attackers '
        'to execute arbitrary code or cause a denial of service via crafted '
        'SSL/TLS handshake messages.',
        'findingArn': 'arn:aws:test789',
        'firstObservedAt': datetime(2022, 5, 4, 16, 23, 3, 692000),
        'inspectorScore': 7.5,
        'inspectorScoreDetails': {
            'adjustedCvss': {
                'adjustments': [],
                'cvssSource': 'NVD',
                'score': 7.5,
                'scoreSource': 'NVD',
                'scoringVector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N',
                'version': '3.1',
            },
        },
        'lastObservedAt': datetime(2022, 5, 4, 16, 23, 3, 692000),
        'packageVulnerabilityDetails': {
            'cvss': [
                {
                    'baseScore': 7.5,
                    'scoringVector': 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N',
                    'source': 'NVD',
                    'version': '3.1',
                },
            ],
            'referenceUrls': ['https://nvd.nist.gov/vuln/detail/CVE-2023-1234'],
            'relatedVulnerabilities': [],
            'source': 'NVD',
            'sourceUrl': 'https://nvd.nist.gov/vuln/detail/CVE-2023-1234',
            'vendorCreatedAt': datetime(2023, 1, 15, 10, 0),
            'vendorSeverity': 'High',
            'vulnerabilityId': 'CVE-2023-1234',
            'vulnerablePackages': [
                {
                    'arch': 'X86_64',
                    'epoch': 0,
                    'name': 'openssl',
                    'packageManager': 'OS',
                    'release': '1.amzn2',
                    'version': '1.0.2k',
                },
            ],
        },
        'remediation': {'recommendation': {'text': 'Update to the latest version of OpenSSL'}},
        'resources': [{
            'details': {
                'awsEc2Instance': {
                    'iamInstanceProfileArn': 'arn:aws:iam::123456789011:instance-profile/InspectorTestingRole',
                    'imageId': 'ami-00800800',
                    'ipV4Addresses': ['10.0.1.4'],
                    'ipV6Addresses': [],
                    'keyName': 'InspectorTest',
                    'launchedAt': datetime(2022, 5, 4, 16, 15, 41),
                    'platform': 'AMAZON_LINUX_2',
                    'subnetId': 'subnet-11203981029833100',
                    'type': 't2.micro',
                    'vpcId': 'vpc-11203981029822100',
                },
            },
            'id': 'i-88503981029833101',
            'partition': 'aws',
            'region': 'us-west-2',
            'tags': {},
            'type': 'AWS_EC2_INSTANCE',
        }],
        'severity': 'HIGH',
        'status': 'ACTIVE',
        'title': 'CVE-2023-1234 - openssl',
        'type': 'PACKAGE_VULNERABILITY',
        'updatedAt': datetime(2022, 5, 4, 16, 23, 3, 692000),
    },
]
