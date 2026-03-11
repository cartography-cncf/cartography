TEST_ECR_IMAGE_DIGEST = (
    "sha256:ecr0000000000000000000000000000000000000000000000000000000000000"
)
TEST_GITLAB_IMAGE_DIGEST = (
    "sha256:gl00000000000000000000000000000000000000000000000000000000000000"
)
TEST_PUBLIC_IMAGE_ID = "python:3.12-slim"
TEST_UPDATE_TAG = 123456789

# Combined file format for file-based ingestion (sbom + cves in one JSON).
# Generated externally by running:
#   docker scout sbom --format json <image>         -> "sbom"
#   docker scout cves --only-base --format sbom <image> -> "cves"

# Scan result for the ECR image
MOCK_ECR_COMBINED_FILE_DATA = {
    "sbom": {
        "source": {
            "image": {
                "digest": TEST_ECR_IMAGE_DIGEST,
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
    },
    "cves": {
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
    },
}

# Scan result for the GitLab image (distinct digest, same base image + vulns)
MOCK_GITLAB_COMBINED_FILE_DATA = {
    "sbom": {
        "source": {
            "image": {
                "digest": TEST_GITLAB_IMAGE_DIGEST,
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
    },
    "cves": {
        "artifacts": [
            {
                "name": "libssl3",
                "version": "3.0.15-1~deb12u1",
                "purl": "pkg:deb/debian/libssl3@3.0.15-1~deb12u1?arch=amd64&distro=debian-12",
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
        ],
    },
}
