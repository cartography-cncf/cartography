from datetime import datetime

from cartography.intel.aws.inspector import transform_inspector_findings
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK


TEST_UPDATE_TAG = 123456789


def test_transform_inspector_findings_network():
    findings, _packages = transform_inspector_findings(LIST_FINDINGS_NETWORK)
    assert findings == [
        {
            'id': 'arn:aws:test123',
            'arn': 'arn:aws:test123',
            'instanceid': 'i-instanceid',
            'severity': 'INFORMATIONAL',
            'name': 'string',
            'firstobservedat': datetime(2015, 1, 1, 0, 0),
            'updatedat': datetime(2015, 1, 1, 0, 0),
            'awsaccount': '123456789011',
            'description': 'string',
            'cvssscore': 123.0,
            'protocol': 'TCP',
            'portrange': '123-124',
            'portrangeend': 124,
            'portrangebegin': 123,
            'type': 'NETWORK_REACHABILITY',
            'status': 'ACTIVE',
        },
    ]


def test_transform_inspector_findings_package():
    findings, packages = transform_inspector_findings(LIST_FINDINGS_EC2_PACKAGE)
    assert findings == [
        {
            'id': 'arn:aws:test456',
            'arn': 'arn:aws:test456',
            'vulnerabilityid': 'CVE-2017-9059',
            'instanceid': 'i-88503981029833100',
            'severity': 'MEDIUM',
            'name': 'CVE-2017-9059 - kernel-tools, kernel',
            'firstobservedat': datetime(2022, 5, 4, 16, 23, 3, 692000),
            'updatedat': datetime(2022, 5, 4, 16, 23, 3, 692000),
            'awsaccount': '123456789012',
            'description': 'The NFSv4 implementation in the Linux kernel through '
            '4.11.1 allows local users to cause a denial of service '
            '(resource consumption) by leveraging improper channel '
            'callback shutdown when unmounting an NFSv4 filesystem, aka '
            'a "module reference and kernel daemon" leak.',
            'cvssscore': 5.5,
            'type': 'PACKAGE_VULNERABILITY',
            'vulnerabilityid': 'CVE-2017-9059',
            'referenceurls': [],
            'relatedvulnerabilities': [],
            'source': 'REDHAT_CVE',
            'vendorcreatedat': datetime(2017, 4, 25, 17, 0),
            'vendorupdatedat': None,
            'vendorseverity': 'Moderate',
            'sourceurl': 'https://access.redhat.com/security/cve/CVE-2017-9059',
            'status': 'ACTIVE',

            'vulnerablepackageids': [
                'kernel-tools|X86_64|4.9.17|6.29.amzn1|0',
                'kernel|X86_64|4.9.17|6.29.amzn1|0',
            ],
        },
        {
            'id': 'arn:aws:test789',
            'arn': 'arn:aws:test789',
            'vulnerabilityid': 'CVE-2023-1234',
            'instanceid': 'i-88503981029833101',
            'severity': 'HIGH',
            'name': 'CVE-2023-1234 - openssl',
            'firstobservedat': datetime(2022, 5, 4, 16, 23, 3, 692000),
            'updatedat': datetime(2022, 5, 4, 16, 23, 3, 692000),
            'awsaccount': '123456789011',
            'description': 'A buffer overflow vulnerability in OpenSSL allows remote attackers '
            'to execute arbitrary code or cause a denial of service via crafted '
            'SSL/TLS handshake messages.',
            'cvssscore': 7.5,
            'type': 'PACKAGE_VULNERABILITY',
            'referenceurls': ['https://nvd.nist.gov/vuln/detail/CVE-2023-1234'],
            'relatedvulnerabilities': [],
            'source': 'NVD',
            'vendorcreatedat': datetime(2023, 1, 15, 10, 0),
            'vendorupdatedat': None,
            'vendorseverity': 'High',
            'sourceurl': 'https://nvd.nist.gov/vuln/detail/CVE-2023-1234',
            'status': 'ACTIVE',

            'vulnerablepackageids': [
                'openssl|X86_64|1.0.2k|1.amzn2|0',
            ],
        },
    ]
    assert packages == [
        {
            'arch': 'X86_64',
            'awsaccount': '123456789012',
            'epoch': 0,
            'filepath': None,
            'findingarn': 'arn:aws:test456',
            'fixedinversion': None,
            'id': 'kernel-tools|X86_64|4.9.17|6.29.amzn1|0',
            'manager': 'OS',
            'name': 'kernel-tools',
            'release': '6.29.amzn1',
            'sourcelayerhash': None,
            'version': '4.9.17',
        },
        {
            'arch': 'X86_64',
            'awsaccount': '123456789012',
            'epoch': 0,
            'filepath': None,
            'findingarn': 'arn:aws:test456',
            'fixedinversion': None,
            'id': 'kernel|X86_64|4.9.17|6.29.amzn1|0',
            'manager': 'OS',
            'name': 'kernel',
            'release': '6.29.amzn1',
            'sourcelayerhash': None,
            'version': '4.9.17',
        },
        {
            'arch': 'X86_64',
            'awsaccount': '123456789011',
            'epoch': 0,
            'filepath': None,
            'findingarn': 'arn:aws:test789',
            'fixedinversion': None,
            'id': 'openssl|X86_64|1.0.2k|1.amzn2|0',
            'manager': 'OS',
            'name': 'openssl',
            'release': '1.amzn2',
            'sourcelayerhash': None,
            'version': '1.0.2k',
        },
    ]
