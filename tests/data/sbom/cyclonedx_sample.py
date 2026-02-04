"""
Sample CycloneDX SBOM test data.

This sample represents a small container image with:
- A root component (the application itself)
- Direct dependencies (express, lodash)
- Transitive dependencies (accepts, mime-types - pulled in by express)

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
