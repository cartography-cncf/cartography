"""Sample Trivy scan results for GitLab container images.

Test coverage:
1. TRIVY_GITLAB_SAMPLE - Single-arch image with single RepoDigests entry
2. TRIVY_GITLAB_MULTIARCH_MANIFEST_LIST - Scan of manifest list itself
3. TRIVY_GITLAB_MULTIARCH_CHILD_AMD64 - Scan of platform-specific child (amd64)
4. TRIVY_GITLAB_MULTIARCH_CHILD_ARM64 - Scan of platform-specific child (arm64)
5. TRIVY_GITLAB_MULTI_REPO_DIGESTS - Multiple RepoDigests entries (tests selection logic)
"""

# Test Case 1: Single-arch image with single RepoDigests entry
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
                        "UID": "a1b2c3d4e5f6g7h8",
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
                    "CweIDs": ["CWE-295"],
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            "V3Score": 7.5,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-99999",
                        "https://nvd.nist.gov/vuln/detail/CVE-2024-99999",
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
                        "UID": "b2c3d4e5f6g7h8i9",
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
                    "CweIDs": ["CWE-119", "CWE-787"],
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
                            "V3Score": 5.4,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-88888",
                        "https://curl.se/docs/CVE-2024-88888.html",
                    ],
                    "PublishedDate": "2024-02-01T00:00:00Z",
                    "LastModifiedDate": "2024-02-10T00:00:00Z",
                },
            ],
        },
    ],
}

# Test Case 2: Scan of multi-arch manifest list itself
# Tests that findings link to the manifest list node (type="manifest_list")
# Uses digest: sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444
TRIVY_GITLAB_MULTIARCH_MANIFEST_LIST = {
    "SchemaVersion": 2,
    "CreatedAt": "2025-05-17T14:00:00.000000-07:00",
    "ArtifactName": "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0",
    "ArtifactType": "container_image",
    "Metadata": {
        "Size": 104857600,
        "OS": {"Family": "debian", "Name": "12.8"},
        "ImageID": "sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444",
        "DiffIDs": [
            "sha256:manifestlist111222333444555666777888999000aaabbbcccdddeeefff",
        ],
        "RepoTags": ["registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0"],
        "RepoDigests": [
            "registry.gitlab.example.com/myorg/awesome-project/app@sha256:bbb222333444555666777888999000aaabbbcccdddeeefff000111222333444"
        ],
        "ImageConfig": {
            "architecture": "amd64",  # Note: manifest list reports a default platform
            "os": "linux",
        },
    },
    "Results": [
        {
            "Target": "registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0 (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-77777",
                    "PkgID": "libgnutls30@3.7.9-2+deb12u3",
                    "PkgName": "libgnutls30",
                    "PkgIdentifier": {
                        "PURL": "pkg:deb/debian/libgnutls30@3.7.9-2+deb12u3?arch=amd64&distro=debian-12.8",
                    },
                    "InstalledVersion": "3.7.9-2+deb12u3",
                    "FixedVersion": "3.7.9-2+deb12u4",
                    "Status": "fixed",
                    "Layer": {
                        "Digest": "sha256:manifestlist111222333444555666777888999000aaabbbcccdddeeefff",
                        "DiffID": "sha256:manifestlist111222333444555666777888999000aaabbbcccdddeeefff",
                    },
                    "SeveritySource": "nvd",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-77777",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Test vulnerability for manifest list",
                    "Description": "Test vulnerability affecting manifest list.",
                    "Severity": "HIGH",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N",
                            "V3Score": 7.5,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-77777",
                    ],
                    "PublishedDate": "2024-03-01T00:00:00Z",
                    "LastModifiedDate": "2024-03-10T00:00:00Z",
                },
            ],
        },
    ],
}

# Test Case 3: Scan of platform-specific child image (linux/amd64)
# Tests that findings link to the child image node when scanning a specific platform
# Uses digest: sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444
TRIVY_GITLAB_MULTIARCH_CHILD_AMD64 = {
    "SchemaVersion": 2,
    "CreatedAt": "2025-05-17T14:15:00.000000-07:00",
    "ArtifactName": "registry.gitlab.example.com/myorg/awesome-project/app@sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
    "ArtifactType": "container_image",
    "Metadata": {
        "Size": 104857600,
        "OS": {"Family": "debian", "Name": "12.8"},
        "ImageID": "sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444",
        "DiffIDs": [
            "sha256:childamd64layer111222333444555666777888999000aaabbbcccdddeeefff",
        ],
        "RepoTags": ["registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0"],
        "RepoDigests": [
            "registry.gitlab.example.com/myorg/awesome-project/app@sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444"
        ],
        "ImageConfig": {
            "architecture": "amd64",
            "os": "linux",
        },
    },
    "Results": [
        {
            "Target": "registry.gitlab.example.com/myorg/awesome-project/app@sha256:child1amd64555666777888999000aaabbbcccdddeeefff000111222333444 (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-66666",
                    "PkgID": "zlib1g@1:1.2.13.dfsg-1",
                    "PkgName": "zlib1g",
                    "PkgIdentifier": {
                        "PURL": "pkg:deb/debian/zlib1g@1:1.2.13.dfsg-1?arch=amd64&distro=debian-12.8",
                    },
                    "InstalledVersion": "1:1.2.13.dfsg-1",
                    "FixedVersion": "1:1.2.13.dfsg-2",
                    "Status": "fixed",
                    "Layer": {
                        "Digest": "sha256:childamd64layer111222333444555666777888999000aaabbbcccdddeeefff",
                        "DiffID": "sha256:childamd64layer111222333444555666777888999000aaabbbcccdddeeefff",
                    },
                    "SeveritySource": "nvd",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-66666",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Test vulnerability for amd64 child image",
                    "Description": "Test vulnerability affecting amd64 platform.",
                    "Severity": "MEDIUM",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:N/I:N/A:H",
                            "V3Score": 5.5,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-66666",
                    ],
                    "PublishedDate": "2024-04-01T00:00:00Z",
                    "LastModifiedDate": "2024-04-10T00:00:00Z",
                },
            ],
        },
    ],
}

# Test Case 4: Scan of platform-specific child image (linux/arm64)
# Tests that findings link to the arm64 child image node
# Uses digest: sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444
TRIVY_GITLAB_MULTIARCH_CHILD_ARM64 = {
    "SchemaVersion": 2,
    "CreatedAt": "2025-05-17T14:30:00.000000-07:00",
    "ArtifactName": "registry.gitlab.example.com/myorg/awesome-project/app@sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
    "ArtifactType": "container_image",
    "Metadata": {
        "Size": 104857600,
        "OS": {"Family": "debian", "Name": "12.8"},
        "ImageID": "sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444",
        "DiffIDs": [
            "sha256:childarm64layer111222333444555666777888999000aaabbbcccdddeeefff",
        ],
        "RepoTags": ["registry.gitlab.example.com/myorg/awesome-project/app:v1.0.0"],
        "RepoDigests": [
            "registry.gitlab.example.com/myorg/awesome-project/app@sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444"
        ],
        "ImageConfig": {
            "architecture": "arm64",
            "os": "linux",
            "variant": "v8",
        },
    },
    "Results": [
        {
            "Target": "registry.gitlab.example.com/myorg/awesome-project/app@sha256:child2arm64555666777888999000aaabbbcccdddeeefff000111222333444 (debian 12.8)",
            "Class": "os-pkgs",
            "Type": "debian",
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2024-55555",
                    "PkgID": "libc6@2.36-9+deb12u4",
                    "PkgName": "libc6",
                    "PkgIdentifier": {
                        "PURL": "pkg:deb/debian/libc6@2.36-9+deb12u4?arch=arm64&distro=debian-12.8",
                    },
                    "InstalledVersion": "2.36-9+deb12u4",
                    "FixedVersion": "2.36-9+deb12u5",
                    "Status": "fixed",
                    "Layer": {
                        "Digest": "sha256:childarm64layer111222333444555666777888999000aaabbbcccdddeeefff",
                        "DiffID": "sha256:childarm64layer111222333444555666777888999000aaabbbcccdddeeefff",
                    },
                    "SeveritySource": "nvd",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-55555",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Test vulnerability for arm64 child image",
                    "Description": "Test vulnerability affecting arm64 platform.",
                    "Severity": "CRITICAL",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                            "V3Score": 9.8,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-55555",
                    ],
                    "PublishedDate": "2024-05-01T00:00:00Z",
                    "LastModifiedDate": "2024-05-10T00:00:00Z",
                },
            ],
        },
    ],
}

# Test Case 5: Scan with multiple RepoDigests entries
# Tests which digest gets selected when multiple are present (should use first one)
# Uses the same image as TRIVY_GITLAB_SAMPLE but with multiple RepoDigests
TRIVY_GITLAB_MULTI_REPO_DIGESTS = {
    "SchemaVersion": 2,
    "CreatedAt": "2025-05-17T14:45:00.000000-07:00",
    "ArtifactName": "registry.gitlab.example.com/myorg/awesome-project/app:latest",
    "ArtifactType": "container_image",
    "Metadata": {
        "Size": 104857600,
        "OS": {"Family": "debian", "Name": "12.8"},
        "ImageID": "sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
        "DiffIDs": [
            "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
        ],
        "RepoTags": [
            "registry.gitlab.example.com/myorg/awesome-project/app:latest",
            "registry.gitlab.example.com/myorg/awesome-project/app:2.0.0",
        ],
        "RepoDigests": [
            # First entry should be used
            "registry.gitlab.example.com/myorg/awesome-project/app@sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
            # Additional entries (should be ignored)
            "registry.gitlab.example.com/different-registry/app@sha256:aaa111222333444555666777888999000aaabbbcccdddeeefff000111222333",
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
                    "VulnerabilityID": "CVE-2024-44444",
                    "PkgID": "bash@5.2.15-2+b2",
                    "PkgName": "bash",
                    "PkgIdentifier": {
                        "PURL": "pkg:deb/debian/bash@5.2.15-2+b2?arch=amd64&distro=debian-12.8",
                    },
                    "InstalledVersion": "5.2.15-2+b2",
                    "FixedVersion": "5.2.15-2+b3",
                    "Status": "fixed",
                    "Layer": {
                        "Digest": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
                        "DiffID": "sha256:layer1111222333444555666777888999000aaabbbcccdddeeefff00011122",
                    },
                    "SeveritySource": "nvd",
                    "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2024-44444",
                    "DataSource": {
                        "ID": "debian",
                        "Name": "Debian Security Tracker",
                        "URL": "https://security-tracker.debian.org/tracker/",
                    },
                    "Title": "Test vulnerability with multiple RepoDigests",
                    "Description": "Test vulnerability for multi-RepoDigests scenario.",
                    "Severity": "LOW",
                    "CVSS": {
                        "nvd": {
                            "V3Vector": "CVSS:3.1/AV:L/AC:H/PR:L/UI:N/S:U/C:L/I:N/A:N",
                            "V3Score": 2.5,
                        },
                    },
                    "References": [
                        "https://example.com/cve-2024-44444",
                    ],
                    "PublishedDate": "2024-06-01T00:00:00Z",
                    "LastModifiedDate": "2024-06-10T00:00:00Z",
                },
            ],
        },
    ],
}
