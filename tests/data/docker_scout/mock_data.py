TEST_IMAGE = "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-app:latest"
TEST_IMAGE_DIGEST = (
    "sha256:0000000000000000000000000000000000000000000000000000000000000000"
)
TEST_PUBLIC_IMAGE_ID = "python:3.12-slim"
TEST_UPDATE_TAG = 123456789

# GitLab container image ID matching the scanned image digest
TEST_GITLAB_IMAGE_ID = TEST_IMAGE_DIGEST

# Mock response from `docker scout sbom --format json <image>`
MOCK_SBOM_DATA = {
    "source": {
        "image": {
            "digest": TEST_IMAGE_DIGEST,
            "manifest": {
                "annotations": {
                    "org.opencontainers.image.base.name": "python:3.12-slim",
                    "org.opencontainers.image.base.digest": "sha256:basedigest000000000000000000000000000000000000000000000000000000",
                    "org.opencontainers.image.version": "3.12",
                },
            },
        },
    },
    "artifacts": [],
}

# Mock response from `docker scout sbom --format json python:3.12-slim` (the public image)
MOCK_PUBLIC_SBOM_DATA = {
    "source": {
        "image": {
            "digest": "sha256:publicdigest00000000000000000000000000000000000000000000000000",
        },
    },
    "artifacts": [
        {
            "name": "libssl3",
            "version": "3.0.15-1~deb12u1",
            "type": "deb",
            "namespace": "debian",
            "purl": "pkg:deb/debian/libssl3@3.0.15-1~deb12u1?arch=amd64&distro=debian-12",
            "locations": [
                {
                    "digest": "sha256:layer1000000000000000000000000000000000000000000000000000000000",
                    "diff_id": "sha256:diff1000000000000000000000000000000000000000000000000000000000",
                },
            ],
        },
        {
            "name": "curl",
            "version": "7.88.1-10+deb12u8",
            "type": "deb",
            "namespace": "debian",
            "purl": "pkg:deb/debian/curl@7.88.1-10+deb12u8?arch=amd64&distro=debian-12",
            "locations": [
                {
                    "digest": "sha256:layer2000000000000000000000000000000000000000000000000000000000",
                    "diff_id": "sha256:diff2000000000000000000000000000000000000000000000000000000000",
                },
            ],
        },
        {
            "name": "bash",
            "version": "5.2.15-2+b2",
            "type": "deb",
            "namespace": "debian",
            "purl": "pkg:deb/debian/bash@5.2.15-2+b2?arch=amd64&distro=debian-12",
            "locations": [
                {
                    "digest": "sha256:layer1000000000000000000000000000000000000000000000000000000000",
                    "diff_id": "sha256:diff1000000000000000000000000000000000000000000000000000000000",
                },
            ],
        },
    ],
}

# Mock response from `docker scout cves --only-base --format sbom <image>`
MOCK_CVES_DATA = {
    "artifacts": [
        {
            "name": "libssl3",
            "version": "3.0.15-1~deb12u1",
            "purl": "pkg:deb/debian/libssl3@3.0.15-1~deb12u1?arch=amd64&distro=debian-12",
        },
        {
            "name": "curl",
            "version": "7.88.1-10+deb12u8",
            "purl": "pkg:deb/debian/curl@7.88.1-10+deb12u8?arch=amd64&distro=debian-12",
        },
    ],
    "vulnerabilities": [
        {
            "purl": "pkg:deb/debian/libssl3@3.0.15-1~deb12u1?arch=amd64&distro=debian-12",
            "vulnerabilities": [
                {
                    "source_id": "CVE-2024-13176",
                    "source": "NVD",
                    "description": "Issue in OpenSSL timing side channel",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-13176",
                    "published_at": "2024-01-15T00:00:00Z",
                    "updated_at": "2024-02-01T00:00:00Z",
                    "cvss": {"severity": "MEDIUM", "version": "3.1"},
                    "vulnerable_range": "<3.0.16-1~deb12u1",
                    "cwes": [{"cwe_id": "CWE-208"}],
                    "epss": {"score": 0.00234, "percentile": 0.6123},
                    "fixed_by": "3.0.16-1~deb12u1",
                },
            ],
        },
        {
            "purl": "pkg:deb/debian/curl@7.88.1-10+deb12u8?arch=amd64&distro=debian-12",
            "vulnerabilities": [
                {
                    "source_id": "CVE-2024-99999",
                    "source": "NVD",
                    "description": "Buffer overflow in curl HTTP/2 handling",
                    "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-99999",
                    "published_at": "2024-03-01T00:00:00Z",
                    "updated_at": "2024-03-15T00:00:00Z",
                    "cvss": {"severity": "HIGH", "version": "3.1"},
                    "vulnerable_range": "<7.88.1-10+deb12u9",
                    "epss": {"score": 0.512, "percentile": 0.912},
                },
            ],
        },
    ],
}
