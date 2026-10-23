TRIVY_VM_SAMPLE = {
    "SchemaVersion": 2,
    "ArtifactName": "ebs:snap-temporary",
    "ArtifactType": "vm",
    "Metadata": {
        "OS": {"Family": "ubuntu", "Name": "20.04"},
        "FilesystemSnapshotId": "aws:ec2-rootfs:i-01",
    },
    "Results": [
        {
            "Target": "ebs:snap-temporary (ubuntu 20.04)",
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
