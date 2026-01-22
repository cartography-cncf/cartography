"""Sample Trivy scan result for a GitLab container image."""

# This sample uses the same digest as the first image in container_registry.py test data
# sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333
TRIVY_GITLAB_SAMPLE = {
    "SchemaVersion": 2,
    "CreatedAt": "2025-05-17T13:51:07.592255-07:00",
    "ArtifactName": "registry.gitlab.example.com/myorg/awesome-project/app:latest",
    "ArtifactType": "container_image",
    "Metadata": {
        "Size": 104857600,
        "OS": {"Family": "debian", "Name": "12.8"},
        "ImageID": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "DiffIDs": [
            "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
        ],
        "RepoTags": ["registry.gitlab.example.com/myorg/awesome-project/app:latest"],
        "RepoDigests": [
            "registry.gitlab.example.com/myorg/awesome-project/app@sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333"
        ],
        "ImageConfig": {
            "architecture": "amd64",
            "os": "linux",
        },
    },
    "Results": [
        {
            "Target": "registry.gitlab.example.com/myorg/awesome-project/app:latest (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-99999",
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
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-99999",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Test vulnerability for GitLab Trivy integration",
                    "Description": "A test vulnerability used for integration testing.",
                    "Severity": "HIGH",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            "V3Score": 7.5,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-99999",
                    ],
                    "PublishedDate": "2024-01-15T00:00:00Z",
                    "LastModifiedDate": "2024-01-20T00:00:00Z",
                },
                {
                    "VulnerabilityID": "CVE-2024-88888",
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
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-88888",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Another test vulnerability for GitLab Trivy integration",
                    "Description": "Another test vulnerability used for integration testing.",
                    "Severity": "MEDIUM",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
                            "V3Score": 5.4,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-88888",
                    ],
                    "PublishedDate": "2024-02-01T00:00:00Z",
                    "LastModifiedDate": "2024-02-10T00:00:00Z",
                },
            ],
        },
    ],
}
