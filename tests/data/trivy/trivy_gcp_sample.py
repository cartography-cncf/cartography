"""Sample Trivy scan result for a GCP Artifact Registry container image."""

# This sample uses a platform-specific digest (sha256:def456) to test multi-arch matching.
# The manifest list digest in artifact_registry.py is sha256:abc123.
# Trivy scans the linux/amd64 platform and reports its specific digest sha256:def456.
TRIVY_GCP_SAMPLE = {
    "SchemaVersion": 2,
    "CreatedAt": "2025-05-17T13:51:07.592255-07:00",
    "ArtifactName": "us-central1-docker.pkg.dev/test-project/docker-repo/my-app:latest",
    "ArtifactType": "container_image",
    "Metadata": {
        "Size": 50000000,
        "OS": {"Family": "debian", "Name": "12.8"},
        "ImageID": "sha256:def456",
        "DiffIDs": [
            "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
        ],
        "RepoTags": [
            "us-central1-docker.pkg.dev/test-project/docker-repo/my-app:latest",
            "us-central1-docker.pkg.dev/test-project/docker-repo/my-app:v1.0.0",
        ],
        "RepoDigests": [
            "us-central1-docker.pkg.dev/test-project/docker-repo/my-app@sha256:def456"
        ],
        "ImageConfig": {
            "architecture": "amd64",
            "os": "linux",
        },
    },
    "Results": [
        {
            "Target": "us-central1-docker.pkg.dev/test-project/docker-repo/my-app:latest (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-77777",
                    "PkgID": "openssl@3.0.15-1~deb12u1",
                    "PkgName": "openssl",
                    "PkgIdentifier": {
                        "PURL": "pkg:deb/debian/openssl@3.0.15-1~deb12u1?arch=amd64&distro=debian-12.8",
                    },
                    "InstalledVersion": "3.0.15-1~deb12u1",
                    "FixedVersion": "3.0.16-1~deb12u1",
                    "Status": "fixed",
                    "Layer": {
                        "Digest": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
                        "DiffID": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
                    },
                    "SeveritySource": "nvd",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-77777",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Test vulnerability for GCP Trivy integration",
                    "Description": "A test vulnerability used for integration testing.",
                    "Severity": "CRITICAL",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                            "V3Score": 9.8,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-77777",
                    ],
                    "PublishedDate": "2024-03-01T00:00:00Z",
                    "LastModifiedDate": "2024-03-05T00:00:00Z",
                },
                {
                    "VulnerabilityID": "CVE-2024-66666",
                    "PkgID": "curl@7.88.1-10+deb12u5",
                    "PkgName": "curl",
                    "PkgIdentifier": {
                        "PURL": "pkg:deb/debian/curl@7.88.1-10+deb12u5?arch=amd64&distro=debian-12.8",
                    },
                    "InstalledVersion": "7.88.1-10+deb12u5",
                    "FixedVersion": "7.88.1-10+deb12u6",
                    "Status": "fixed",
                    "Layer": {
                        "Digest": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
                        "DiffID": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
                    },
                    "SeveritySource": "nvd",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-66666",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Another test vulnerability for GCP Trivy integration",
                    "Description": "Another test vulnerability used for integration testing.",
                    "Severity": "HIGH",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            "V3Score": 7.5,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-66666",
                    ],
                    "PublishedDate": "2024-03-10T00:00:00Z",
                    "LastModifiedDate": "2024-03-15T00:00:00Z",
                },
            ],
        },
    ],
}
