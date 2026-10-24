TRIVY_VM_SAMPLE = {
    "SchemaVersion": 2,
    "Trivy": {"Version": "0.76.1"},
    "CreatedAt": "2026-10-23T12:00:00Z",
    "ArtifactName": "snap-temporary",
    "ArtifactType": "vm",
    "Metadata": {
        "OS": {"Family": "ubuntu", "Name": "20.04"},
        "FilesystemSnapshotId": "aws:ec2:i-01:rootfs",
    },
    "Results": [
        {
            "Target": "snap-temporary (ubuntu 20.04)",
            "Class": "os-pkgs",
            "Type": "ubuntu",
            "Packages": [
                {"Name": "example-package", "Version": "1.0.0"},
                {"Name": "clean-package", "Version": "2.0.0"},
            ],
            "Vulnerabilities": [
                {
                    "VulnerabilityID": "CVE-2026-12345",
                    "PkgName": "example-package",
                    "InstalledVersion": "1.0.0",
                    "FixedVersion": "1.0.1",
                    "Severity": "HIGH",
                },
            ],
        },
    ],
}
