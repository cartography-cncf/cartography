"""
Sample CycloneDX SBOM test data with vulnerabilities.

This sample represents a small container image with:
- A root component (the application itself)
- Direct dependencies (express, lodash)
- Transitive dependencies (accepts, mime-types - pulled in by express)
- Vulnerabilities affecting some packages

Package ID format: {version}|{name} (matches Trivy format)
"""

CYCLONEDX_SBOM_SAMPLE = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
    "version": 1,
    "metadata": {
        "timestamp": "2025-01-15T12:00:00Z",
        "component": {
            "bom-ref": "root-app",
            "type": "application",
            "name": "my-test-app",
            "version": "1.0.0",
            "purl": "pkg:docker/my-test-app@1.0.0",
            "properties": [
                {
                    "name": "aquasecurity:trivy:RepoDigest",
                    "value": "000000000000.dkr.ecr.us-east-1.amazonaws.com/my-test-app@sha256:abc123def456789",
                }
            ],
        },
    },
    "components": [
        {
            "bom-ref": "pkg:npm/express@4.17.1",
            "type": "library",
            "name": "express",
            "version": "4.17.1",
            "purl": "pkg:npm/express@4.17.1",
        },
        {
            "bom-ref": "pkg:npm/lodash@4.17.20",
            "type": "library",
            "name": "lodash",
            "version": "4.17.20",
            "purl": "pkg:npm/lodash@4.17.20",
        },
        {
            "bom-ref": "pkg:npm/accepts@1.3.7",
            "type": "library",
            "name": "accepts",
            "version": "1.3.7",
            "purl": "pkg:npm/accepts@1.3.7",
        },
        {
            "bom-ref": "pkg:npm/mime-types@2.1.27",
            "type": "library",
            "name": "mime-types",
            "version": "2.1.27",
            "purl": "pkg:npm/mime-types@2.1.27",
        },
        {
            "bom-ref": "pkg:npm/body-parser@1.19.0",
            "type": "library",
            "name": "body-parser",
            "version": "1.19.0",
            "purl": "pkg:npm/body-parser@1.19.0",
        },
    ],
    "dependencies": [
        {
            "ref": "root-app",
            "dependsOn": [
                "pkg:npm/express@4.17.1",
                "pkg:npm/lodash@4.17.20",
            ],
        },
        {
            "ref": "pkg:npm/express@4.17.1",
            "dependsOn": [
                "pkg:npm/accepts@1.3.7",
                "pkg:npm/body-parser@1.19.0",
            ],
        },
        {
            "ref": "pkg:npm/accepts@1.3.7",
            "dependsOn": [
                "pkg:npm/mime-types@2.1.27",
            ],
        },
        {
            "ref": "pkg:npm/lodash@4.17.20",
            "dependsOn": [],
        },
        {
            "ref": "pkg:npm/mime-types@2.1.27",
            "dependsOn": [],
        },
        {
            "ref": "pkg:npm/body-parser@1.19.0",
            "dependsOn": [],
        },
    ],
    "vulnerabilities": [
        {
            "id": "CVE-2021-23337",
            "source": {
                "name": "NVD",
                "url": "https://nvd.nist.gov/vuln/detail/CVE-2021-23337",
            },
            "description": "Lodash versions prior to 4.17.21 are vulnerable to Command Injection via the template function.",
            "ratings": [
                {
                    "source": {"name": "NVD"},
                    "score": 7.2,
                    "severity": "HIGH",
                    "method": "CVSSv3",
                    "vector": "CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H",
                }
            ],
            "cwes": [
                {"id": "CWE-94"},
            ],
            "references": [
                {"url": "https://nvd.nist.gov/vuln/detail/CVE-2021-23337"},
                {"url": "https://github.com/lodash/lodash/issues/5085"},
            ],
            "affects": [
                {"ref": "pkg:npm/lodash@4.17.20"},
            ],
            "published": "2021-02-15T10:00:00Z",
            "updated": "2021-06-21T08:00:00Z",
        },
        {
            "id": "CVE-2020-28500",
            "source": {
                "name": "NVD",
                "url": "https://nvd.nist.gov/vuln/detail/CVE-2020-28500",
            },
            "description": "Lodash versions prior to 4.17.21 are vulnerable to Regular Expression Denial of Service (ReDoS) via the toNumber, trim and trimEnd functions.",
            "ratings": [
                {
                    "source": {"name": "NVD"},
                    "score": 5.3,
                    "severity": "MEDIUM",
                    "method": "CVSSv3",
                    "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L",
                }
            ],
            "cwes": [
                {"id": "CWE-1333"},
            ],
            "references": [
                {"url": "https://nvd.nist.gov/vuln/detail/CVE-2020-28500"},
            ],
            "affects": [
                {"ref": "pkg:npm/lodash@4.17.20"},
            ],
            "published": "2021-02-15T10:00:00Z",
            "updated": "2021-06-21T08:00:00Z",
        },
        {
            "id": "CVE-2022-24999",
            "source": {
                "name": "NVD",
                "url": "https://nvd.nist.gov/vuln/detail/CVE-2022-24999",
            },
            "description": "qs before 6.10.3, as used in Express before 4.17.3 and other products, allows attackers to cause a denial of service via malformed URL.",
            "ratings": [
                {
                    "source": {"name": "NVD"},
                    "score": 7.5,
                    "severity": "HIGH",
                    "method": "CVSSv3",
                    "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                }
            ],
            "cwes": [
                {"id": "CWE-1321"},
            ],
            "references": [
                {"url": "https://nvd.nist.gov/vuln/detail/CVE-2022-24999"},
            ],
            "affects": [
                {"ref": "pkg:npm/express@4.17.1"},
            ],
            "published": "2022-11-26T10:00:00Z",
            "updated": "2022-12-05T08:00:00Z",
        },
    ],
}


# Test image digest extracted from the sample
TEST_IMAGE_DIGEST = "sha256:abc123def456789"

# Expected direct dependencies (referenced by root component)
EXPECTED_DIRECT_DEPS = {
    "pkg:npm/express@4.17.1",
    "pkg:npm/lodash@4.17.20",
}

# Expected transitive dependencies
EXPECTED_TRANSITIVE_DEPS = {
    "pkg:npm/accepts@1.3.7",
    "pkg:npm/mime-types@2.1.27",
    "pkg:npm/body-parser@1.19.0",
}

# Expected package IDs in Trivy format: {version}|{name}
EXPECTED_PACKAGE_IDS = {
    "4.17.1|express",
    "4.17.20|lodash",
    "1.3.7|accepts",
    "2.1.27|mime-types",
    "1.19.0|body-parser",
}

# Expected DEPENDS_ON relationships (source_id, depends_on_id) in Trivy format
EXPECTED_DEPENDENCY_RELS = {
    # express depends on accepts and body-parser
    ("4.17.1|express", "1.3.7|accepts"),
    ("4.17.1|express", "1.19.0|body-parser"),
    # accepts depends on mime-types
    ("1.3.7|accepts", "2.1.27|mime-types"),
}

# Minimal SBOM for edge case testing
MINIMAL_SBOM = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "components": [
        {
            "bom-ref": "pkg:npm/simple@1.0.0",
            "type": "library",
            "name": "simple",
            "version": "1.0.0",
            "purl": "pkg:npm/simple@1.0.0",
        },
    ],
}

# Invalid SBOM (missing bomFormat)
INVALID_SBOM_MISSING_FORMAT = {
    "specVersion": "1.5",
    "components": [],
}

# Invalid SBOM (wrong format)
INVALID_SBOM_WRONG_FORMAT = {
    "bomFormat": "SPDX",
    "specVersion": "2.3",
    "components": [],
}

# SBOM without dependencies (all packages treated as direct)
SBOM_NO_DEPENDENCIES = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "components": [
        {
            "bom-ref": "pkg:npm/pkg-a@1.0.0",
            "type": "library",
            "name": "pkg-a",
            "version": "1.0.0",
            "purl": "pkg:npm/pkg-a@1.0.0",
        },
        {
            "bom-ref": "pkg:npm/pkg-b@2.0.0",
            "type": "library",
            "name": "pkg-b",
            "version": "2.0.0",
            "purl": "pkg:npm/pkg-b@2.0.0",
        },
    ],
}
