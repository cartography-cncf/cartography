from datetime import datetime

from cartography.intel.aws.inspector import transform_inspector_findings
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK

TEST_UPDATE_TAG = 123456789


def test_transform_inspector_findings_network():
    findings, _packages, _finding_to_package_map = transform_inspector_findings(
        LIST_FINDINGS_NETWORK
    )
    assert findings == [
        {
            "id": "arn:aws:test123",
            "arn": "arn:aws:test123",
            "instanceid": "i-instanceid",
            "severity": "INFORMATIONAL",
            "name": "string",
            "firstobservedat": datetime(2015, 1, 1, 0, 0),
            "updatedat": datetime(2015, 1, 1, 0, 0),
            "awsaccount": "123456789011",
            "description": "string",
            "cvssscore": 123.0,
            "protocol": "TCP",
            "portrange": "123-124",
            "portrangeend": 124,
            "portrangebegin": 123,
            "type": "NETWORK_REACHABILITY",
            "status": "ACTIVE",
        },
    ]


def test_transform_inspector_findings_package():
    findings, packages, finding_to_package_map = transform_inspector_findings(
        LIST_FINDINGS_EC2_PACKAGE
    )
    assert findings == [
        {
            "id": "arn:aws:test456",
            "arn": "arn:aws:test456",
            "vulnerabilityid": "CVE-2017-9059",
            "instanceid": "i-88503981029833100",
            "severity": "MEDIUM",
            "name": "CVE-2017-9059 - kernel-tools, kernel",
            "firstobservedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "updatedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "awsaccount": "123456789012",
            "description": "The NFSv4 implementation in the Linux kernel through "
            "4.11.1 allows local users to cause a denial of service "
            "(resource consumption) by leveraging improper channel "
            "callback shutdown when unmounting an NFSv4 filesystem, aka "
            'a "module reference and kernel daemon" leak.',
            "cvssscore": 5.5,
            "type": "PACKAGE_VULNERABILITY",
            "vulnerabilityid": "CVE-2017-9059",
            "referenceurls": [],
            "relatedvulnerabilities": [],
            "source": "REDHAT_CVE",
            "vendorcreatedat": datetime(2017, 4, 25, 17, 0),
            "vendorupdatedat": None,
            "vendorseverity": "Moderate",
            "sourceurl": "https://access.redhat.com/security/cve/CVE-2017-9059",
            "status": "ACTIVE",
            "vulnerablepackageids": [
                "kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
                "kernel|0:4.9.17-6.29.amzn1.X86_64",
            ],
        },
        {
            "id": "arn:aws:test789",
            "arn": "arn:aws:test789",
            "vulnerabilityid": "CVE-2023-1234",
            "instanceid": "i-88503981029833101",
            "severity": "HIGH",
            "name": "CVE-2023-1234 - openssl",
            "firstobservedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "updatedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "awsaccount": "123456789011",
            "description": "A buffer overflow vulnerability in OpenSSL allows remote attackers "
            "to execute arbitrary code or cause a denial of service via crafted "
            "SSL/TLS handshake messages.",
            "cvssscore": 7.5,
            "type": "PACKAGE_VULNERABILITY",
            "referenceurls": ["https://nvd.nist.gov/vuln/detail/CVE-2023-1234"],
            "relatedvulnerabilities": [],
            "source": "NVD",
            "vendorcreatedat": datetime(2023, 1, 15, 10, 0),
            "vendorupdatedat": None,
            "vendorseverity": "High",
            "sourceurl": "https://nvd.nist.gov/vuln/detail/CVE-2023-1234",
            "status": "ACTIVE",
            "vulnerablepackageids": [
                "openssl|0:1.0.2k-1.amzn2.X86_64",
            ],
        },
    ]
    # The order of packages is not guaranteed because it comes from a set.
    # To fix this, we sort both the actual and expected lists by a unique key before comparing.
    sorted_packages = sorted(packages, key=lambda p: p["id"])
    expected_packages = [
        {
            "arch": "X86_64",
            "epoch": 0,
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "id": "kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
            "packageManager": "OS",
            "name": "kernel-tools",
            "release": "6.29.amzn1",
            "version": "4.9.17",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
        },
        {
            "arch": "X86_64",
            "epoch": 0,
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "id": "kernel|0:4.9.17-6.29.amzn1.X86_64",
            "packageManager": "OS",
            "name": "kernel",
            "release": "6.29.amzn1",
            "version": "4.9.17",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
        },
        {
            "arch": "X86_64",
            "epoch": 0,
            "id": "openssl|0:1.0.2k-1.amzn2.X86_64",
            "packageManager": "OS",
            "name": "openssl",
            "release": "1.amzn2",
            "version": "1.0.2k",
        },
    ]
    assert sorted_packages == sorted(expected_packages, key=lambda p: p["id"])
    sorted_finding_to_package_map = sorted(
        finding_to_package_map,
        key=lambda i: (i["findingarn"], i["packageid"]),
    )
    expected_finding_to_package_map = [
        {
            "filePath": None,
            "findingarn": "arn:aws:test456",
            "packageid": "kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "sourceLambdaLayerArn": None,
            "sourceLayerHash": None,
        },
        {
            "filePath": None,
            "findingarn": "arn:aws:test456",
            "packageid": "kernel|0:4.9.17-6.29.amzn1.X86_64",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "sourceLambdaLayerArn": None,
            "sourceLayerHash": None,
        },
        {
            "filePath": None,
            "findingarn": "arn:aws:test789",
            "packageid": "openssl|0:1.0.2k-1.amzn2.X86_64",
            "remediation": None,
            "fixedInVersion": None,
            "sourceLambdaLayerArn": None,
            "sourceLayerHash": None,
        },
    ]
    assert sorted_finding_to_package_map == sorted(
        expected_finding_to_package_map,
        key=lambda i: (i["findingarn"], i["packageid"]),
    )
