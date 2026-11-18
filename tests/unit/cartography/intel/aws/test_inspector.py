from datetime import datetime
from typing import Any
from typing import cast

import pytest

from cartography.intel.aws.inspector import transform_ec2_package_findings
from cartography.intel.aws.inspector import transform_inspector_findings
from cartography.intel.aws.inspector import transform_inspector_packages
from cartography.intel.aws.inspector_packages import package_url
from tests.data.aws.inspector import LIST_FINDINGS_EC2_PACKAGE
from tests.data.aws.inspector import LIST_FINDINGS_NETWORK

TEST_UPDATE_TAG = 123456789


def test_transform_inspector_findings_network():
    findings, _packages, _finding_to_package_map, vulnerabilities = (
        transform_inspector_findings(LIST_FINDINGS_NETWORK)
    )
    assert findings == [
        {
            "id": "arn:aws:inspector2:us-west-2:123456789011:finding/0123456789abcdef0123456789abc123",
            "arn": "arn:aws:inspector2:us-west-2:123456789011:finding/0123456789abcdef0123456789abc123",
            "instanceid": "i-instanceid",
            "severity": "INFORMATIONAL",
            "name": "string",
            "firstobservedat": datetime(2015, 1, 1, 0, 0),
            "updatedat": datetime(2015, 1, 1, 0, 0),
            "awsaccount": "123456789011",
            "description": "string",
            "cvssscore": 123.0,
            "cvssvector": "string",
            "protocol": "TCP",
            "portrange": "123-124",
            "portrangeend": 124,
            "portrangebegin": 123,
            "type": "NETWORK_REACHABILITY",
            "status": "ACTIVE",
            "fixavailable": "YES",
            "exploitavailable": "NO",
            "lastknownexploitat": datetime(2015, 1, 1, 0, 0),
            "epss_score_inspector": 123.0,
        },
    ]
    assert vulnerabilities == []


def test_transform_inspector_findings_package():
    findings, packages, finding_to_package_map, vulnerabilities = (
        transform_inspector_findings(LIST_FINDINGS_EC2_PACKAGE)
    )
    assert findings == [
        {
            "id": "arn:aws:inspector2:us-west-2:123456789012:finding/7123456789abcdef0123456789abc456",
            "arn": "arn:aws:inspector2:us-west-2:123456789012:finding/7123456789abcdef0123456789abc456",
            "vulnerabilityid": "CVE-2017-9059",
            "instanceid": "i-88503981029833100",
            "severity": "MEDIUM",
            "name": "CVE-2017-9059 - kernel-tools, kernel",
            "firstobservedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "updatedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "awsaccount": "123456789012",
            "cvssscore": 5.5,
            "cvssvector": "CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H",
            "type": "PACKAGE_VULNERABILITY",
            "vulnerabilityid": "CVE-2017-9059",
            "cve_id": "CVE-2017-9059",
            "vendorseverity": "Moderate",
            "status": "ACTIVE",
            "vulnerablepackageids": [
                "OS|amazon|kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
                "OS|amazon|kernel|0:4.9.17-6.29.amzn1.X86_64",
            ],
            "fixavailable": "PARTIAL",
            "exploitavailable": "YES",
            "lastknownexploitat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "epss_score_inspector": 0.42,
        },
        {
            "id": "arn:aws:inspector2:us-west-2:123456789011:finding/f123456789abcdef0123456789abc789",
            "arn": "arn:aws:inspector2:us-west-2:123456789011:finding/f123456789abcdef0123456789abc789",
            "vulnerabilityid": "CVE-2023-1234",
            "instanceid": "i-88503981029833101",
            "severity": "HIGH",
            "name": "CVE-2023-1234 - openssl",
            "firstobservedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "updatedat": datetime(2022, 5, 4, 16, 23, 3, 692000),
            "awsaccount": "123456789011",
            "cvssscore": 7.5,
            "cvssvector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
            "type": "PACKAGE_VULNERABILITY",
            "cve_id": "CVE-2023-1234",
            "vendorseverity": "High",
            "status": "ACTIVE",
            "vulnerablepackageids": [
                "OS|amazon|openssl|0:1.0.2k-1.amzn2.X86_64",
            ],
            "fixavailable": None,
            "exploitavailable": None,
        },
    ]
    assert vulnerabilities == [
        {
            "id": "CVE-2017-9059",
            "vulnerabilityid": "CVE-2017-9059",
            "cve_id": "CVE-2017-9059",
            "has_cve": "true",
            "description": "The NFSv4 implementation in the Linux kernel through "
            "4.11.1 allows local users to cause a denial of service "
            "(resource consumption) by leveraging improper channel "
            "callback shutdown when unmounting an NFSv4 filesystem, aka "
            'a "module reference and kernel daemon" leak.',
            "referenceurls": [],
            "relatedvulnerabilities": [],
            "vendorcvssvectors": [
                "CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H",
                "AV:L/AC:L/Au:N/C:N/I:N/A:C",
                "CVSS:3.0/AV:L/AC:L/PR:L/UI:N/S:U/C:N/I:N/A:H",
            ],
            "vendorcvssscores": [5.5, 4.9, 5.5],
            "source": "REDHAT_CVE",
            "sourceurl": "https://access.redhat.com/security/cve/CVE-2017-9059",
            "vendorcreatedat": datetime(2017, 4, 25, 17, 0),
            "vendorupdatedat": None,
        },
        {
            "id": "CVE-2023-1234",
            "vulnerabilityid": "CVE-2023-1234",
            "cve_id": "CVE-2023-1234",
            "has_cve": "true",
            "description": "A buffer overflow vulnerability in OpenSSL allows remote attackers "
            "to execute arbitrary code or cause a denial of service via crafted "
            "SSL/TLS handshake messages.",
            "referenceurls": ["https://nvd.nist.gov/vuln/detail/CVE-2023-1234"],
            "relatedvulnerabilities": [],
            "vendorcvssvectors": ["CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"],
            "vendorcvssscores": [7.5],
            "source": "NVD",
            "sourceurl": "https://nvd.nist.gov/vuln/detail/CVE-2023-1234",
            "vendorcreatedat": datetime(2023, 1, 15, 10, 0),
            "vendorupdatedat": None,
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
            "id": "OS|amazon|kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
            "packageManager": "OS",
            "name": "kernel-tools",
            "release": "6.29.amzn1",
            "purl": "pkg:rpm/amazon/kernel-tools@4.9.17-6.29.amzn1?arch=x86_64",
            "type": "rpm",
            "purl_version": "4.9.17-6.29.amzn1",
            "normalized_id": "rpm|amazon/kernel-tools|4.9.17-6.29.amzn1",
            "version": "4.9.17",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
        },
        {
            "arch": "X86_64",
            "epoch": 0,
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "id": "OS|amazon|kernel|0:4.9.17-6.29.amzn1.X86_64",
            "packageManager": "OS",
            "name": "kernel",
            "release": "6.29.amzn1",
            "purl": "pkg:rpm/amazon/kernel@4.9.17-6.29.amzn1?arch=x86_64",
            "type": "rpm",
            "purl_version": "4.9.17-6.29.amzn1",
            "normalized_id": "rpm|amazon/kernel|4.9.17-6.29.amzn1",
            "version": "4.9.17",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
        },
        {
            "arch": "X86_64",
            "epoch": 0,
            "id": "OS|amazon|openssl|0:1.0.2k-1.amzn2.X86_64",
            "packageManager": "OS",
            "name": "openssl",
            "release": "1.amzn2",
            "purl": "pkg:rpm/amazon/openssl@1.0.2k-1.amzn2?arch=x86_64",
            "type": "rpm",
            "purl_version": "1.0.2k-1.amzn2",
            "normalized_id": "rpm|amazon/openssl|1.0.2k-1.amzn2",
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
            "findingarn": "arn:aws:inspector2:us-west-2:123456789012:finding/7123456789abcdef0123456789abc456",
            "packageid": "OS|amazon|kernel-tools|0:4.9.17-6.29.amzn1.X86_64",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "sourceLambdaLayerArn": None,
            "sourceLayerHash": None,
        },
        {
            "filePath": None,
            "findingarn": "arn:aws:inspector2:us-west-2:123456789012:finding/7123456789abcdef0123456789abc456",
            "packageid": "OS|amazon|kernel|0:4.9.17-6.29.amzn1.X86_64",
            "remediation": "Upgrade your installed software packages to the proposed fixed in version and release.\n\nyum update kernel\n\nyum update kernel-tools",
            "fixedInVersion": "0:4.9.18-6.30.amzn1.X86_64",
            "sourceLambdaLayerArn": None,
            "sourceLayerHash": None,
        },
        {
            "filePath": None,
            "findingarn": "arn:aws:inspector2:us-west-2:123456789011:finding/f123456789abcdef0123456789abc789",
            "packageid": "OS|amazon|openssl|0:1.0.2k-1.amzn2.X86_64",
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


def test_transform_inspector_findings_merges_reference_urls_per_vulnerability():
    # Arrange: two findings of one vulnerability on hosts running different
    # distributions, each listing its own distribution's advisory.
    amazon_linux_finding = {
        **LIST_FINDINGS_EC2_PACKAGE[1],
        "findingArn": "arn:aws:inspector2:us-west-2:123456789011:finding/a1",
        "packageVulnerabilityDetails": {
            **LIST_FINDINGS_EC2_PACKAGE[1]["packageVulnerabilityDetails"],
            "referenceUrls": [
                "https://nvd.nist.gov/vuln/detail/CVE-2023-1234",
                "https://alas.aws.amazon.com/AL2023/ALAS2023-2023-001.html",
            ],
        },
    }
    ubuntu_finding = {
        **LIST_FINDINGS_EC2_PACKAGE[1],
        "findingArn": "arn:aws:inspector2:us-west-2:123456789011:finding/a2",
        "packageVulnerabilityDetails": {
            **LIST_FINDINGS_EC2_PACKAGE[1]["packageVulnerabilityDetails"],
            "referenceUrls": [
                "https://ubuntu.com/security/CVE-2023-1234",
                "https://nvd.nist.gov/vuln/detail/CVE-2023-1234",
            ],
        },
    }

    # Act
    findings, _packages, _finding_to_package_map, vulnerabilities = (
        transform_inspector_findings([amazon_linux_finding, ubuntu_finding])
    )

    # Assert
    assert [f["vulnerabilityid"] for f in findings] == ["CVE-2023-1234"] * 2
    assert [(v["id"], v["referenceurls"]) for v in vulnerabilities] == [
        (
            "CVE-2023-1234",
            [
                "https://alas.aws.amazon.com/AL2023/ALAS2023-2023-001.html",
                "https://nvd.nist.gov/vuln/detail/CVE-2023-1234",
                "https://ubuntu.com/security/CVE-2023-1234",
            ],
        ),
    ]


_KERNEL_DETAILS = cast(
    dict[str, Any], LIST_FINDINGS_EC2_PACKAGE[0]["packageVulnerabilityDetails"]
)


@pytest.mark.parametrize(
    ("vulnerability_id", "cve_id", "has_cve"),
    [
        ("CVE-2023-1234", "CVE-2023-1234", "true"),
        ("GHSA-jfh8-c2jp-5v3q", None, "false"),
        ("ALAS2023-2023-001", None, "false"),
    ],
)
def test_transform_inspector_findings_names_only_cves_as_cves(
    vulnerability_id, cve_id, has_cve
):
    finding = LIST_FINDINGS_EC2_PACKAGE[1]
    details = {
        **finding["packageVulnerabilityDetails"],
        "vulnerabilityId": vulnerability_id,
    }

    findings, _packages, _finding_to_package_map, vulnerabilities = (
        transform_inspector_findings(
            [{**finding, "packageVulnerabilityDetails": details}]
        )
    )

    assert findings[0]["vulnerabilityid"] == vulnerability_id
    assert findings[0]["cve_id"] == cve_id
    assert (vulnerabilities[0]["cve_id"], vulnerabilities[0]["has_cve"]) == (
        cve_id,
        has_cve,
    )


@pytest.mark.parametrize(
    "other_instance_changes, shares_content",
    [
        ({}, True),
        ({"firstObservedAt": datetime(2023, 1, 1)}, True),
        (
            {
                "packageVulnerabilityDetails": {
                    **_KERNEL_DETAILS,
                    "vulnerablePackages": _KERNEL_DETAILS["vulnerablePackages"][::-1],
                },
            },
            True,
        ),
        (
            {
                "packageVulnerabilityDetails": {
                    **_KERNEL_DETAILS,
                    "vulnerablePackages": [
                        {
                            **_KERNEL_DETAILS["vulnerablePackages"][0],
                            "fixedInVersion": "9.9",
                        },
                        *_KERNEL_DETAILS["vulnerablePackages"][1:],
                    ],
                },
            },
            False,
        ),
        (
            {
                "inspectorScoreDetails": {
                    "adjustedCvss": {
                        "score": 9.8,
                        "scoringVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    },
                },
            },
            False,
        ),
        ({"fixAvailable": "YES"}, False),
    ],
)
def test_transform_ec2_package_findings_shares_content_across_instances(
    other_instance_changes,
    shares_content,
):
    # Arrange: the same kernel finding on two instances.
    kernel = LIST_FINDINGS_EC2_PACKAGE[0]
    other_instance = {
        **kernel,
        "findingArn": "arn:aws:inspector2:us-west-2:123456789012:finding/" + "b" * 32,
        "resources": [{**kernel["resources"][0], "id": "i-other"}],
        **other_instance_changes,
    }

    # Act
    contents, _packages, _links, _vulnerabilities, finding_contents = (
        transform_ec2_package_findings([kernel, other_instance])
    )

    # Assert
    assert (finding_contents[0][1] == finding_contents[1][1]) is shares_content
    assert len(contents) == (1 if shares_content else 2)


@pytest.mark.parametrize(
    ("package", "platform", "purl"),
    [
        (
            {
                "name": "openssl",
                "version": "1.0.2k",
                "release": "24.amzn2.0.4",
                "epoch": 1,
                "arch": "X86_64",
                "packageManager": "OS",
            },
            "AMAZON_LINUX_2",
            "pkg:rpm/amazon/openssl@1.0.2k-24.amzn2.0.4?arch=x86_64&epoch=1",
        ),
        (
            {
                "name": "curl",
                "version": "7.88.1",
                "release": "10+deb12u5",
                "arch": "X86_64",
                "packageManager": "OS",
            },
            "DEBIAN_12",
            "pkg:deb/debian/curl@7.88.1-10%2Bdeb12u5?arch=amd64",
        ),
        (
            {
                "name": "busybox",
                "version": "1.36.1",
                "release": "r15",
                "packageManager": "OS",
            },
            "ALPINE_LINUX_3_19",
            "pkg:apk/alpine/busybox@1.36.1-r15",
        ),
        (
            {"name": "openssl", "version": "3.0.2", "packageManager": "OS"},
            "WINDOWS_SERVER_2022",
            None,
        ),
        (
            {"name": "requests", "version": "2.28.0", "packageManager": "PIP"},
            None,
            "pkg:pypi/requests@2.28.0",
        ),
        (
            {"name": "@babel/core", "version": "7.22.0", "packageManager": "NPM"},
            None,
            "pkg:npm/%40babel/core@7.22.0",
        ),
        (
            {
                "name": "org.apache.logging.log4j:log4j-core",
                "version": "2.14.1",
                "packageManager": "JAR",
            },
            None,
            "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1",
        ),
        (
            {
                "name": "golang.org/x/net",
                "version": "v0.17.0",
                "packageManager": "GOBINARY",
            },
            None,
            "pkg:golang/golang.org/x/net@v0.17.0",
        ),
        (
            {"name": "hono", "version": "4.12.14", "packageManager": "NODE"},
            None,
            "pkg:npm/hono@4.12.14",
        ),
        (
            {"name": "django", "version": "5.1", "packageManager": "PYTHON"},
            None,
            "pkg:pypi/django@5.1",
        ),
        (
            {
                "name": "io.netty:netty-codec-http",
                "version": "4.1.130.Final",
                "packageManager": "JAVA",
            },
            None,
            "pkg:maven/io.netty/netty-codec-http@4.1.130.Final",
        ),
        (
            {
                "name": "github.com/go-chi/chi/v5",
                "version": "v5.2.2",
                "packageManager": "GO",
            },
            None,
            "pkg:golang/github.com/go-chi/chi/v5@v5.2.2",
        ),
        (
            {"name": "log4j-core", "version": "2.14.1", "packageManager": "JAR"},
            None,
            None,
        ),
        (
            {"name": ":log4j-core", "version": "2.14.1", "packageManager": "JAR"},
            None,
            None,
        ),
        (
            {"name": "org.apache:", "version": "2.14.1", "packageManager": "JAR"},
            None,
            None,
        ),
        ({"name": "thing", "version": "1.0", "packageManager": "GENERIC"}, None, None),
    ],
)
def test_package_url(package, platform, purl):
    assert package_url(package, platform) == purl


@pytest.mark.parametrize(
    ("platform", "package_id"),
    [
        ("DEBIAN_12", "OS|debian|curl|7.88.1-10.X86_64"),
        ("debian", "OS|platform:debian|curl|7.88.1-10.X86_64"),
        (None, "OS|platform:unknown|curl|7.88.1-10.X86_64"),
    ],
)
def test_transform_inspector_packages_keys_os_packages_by_distribution(
    platform, package_id
):
    package = {
        "name": "curl",
        "version": "7.88.1",
        "release": "10",
        "arch": "X86_64",
        "packageManager": "OS",
    }

    packages = transform_inspector_packages({"vulnerablePackages": [package]}, platform)

    assert list(packages) == [package_id]
