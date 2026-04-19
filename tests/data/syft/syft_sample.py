"""
Sample Syft JSON output for testing.

This sample represents a simplified Syft scan of a container image with:
- 5 packages (artifacts)
- Dependency relationships forming a tree:
    - express (root) -> body-parser (direct dep) -> bytes (transitive dep)
    - express (root) -> accepts (direct dep)
    - lodash (root, no dependencies)

Syft relationship semantics:
    {parent: X, child: Y, type: "dependency-of"} means Y depends on X (Y requires X)
"""

from typing import Any

SYFT_SAMPLE = {
    "artifacts": [
        {
            "id": "pkg:npm/express@4.18.2",
            "name": "express",
            "version": "4.18.2",
            "type": "npm",
            "foundBy": "javascript-package-cataloger",
            "locations": [{"path": "/app/node_modules/express/package.json"}],
            "licenses": [{"value": "MIT"}],
            "language": "javascript",
            "cpes": ["cpe:2.3:a:express:express:4.18.2:*:*:*:*:node.js:*:*"],
            "purl": "pkg:npm/express@4.18.2",
            "metadata": {"name": "express", "version": "4.18.2"},
        },
        {
            "id": "pkg:npm/body-parser@1.20.1",
            "name": "body-parser",
            "version": "1.20.1",
            "type": "npm",
            "foundBy": "javascript-package-cataloger",
            "locations": [{"path": "/app/node_modules/body-parser/package.json"}],
            "licenses": [{"value": "MIT"}],
            "language": "javascript",
            "cpes": ["cpe:2.3:a:body-parser:body-parser:1.20.1:*:*:*:*:node.js:*:*"],
            "purl": "pkg:npm/body-parser@1.20.1",
            "metadata": {"name": "body-parser", "version": "1.20.1"},
        },
        {
            "id": "pkg:npm/bytes@3.1.2",
            "name": "bytes",
            "version": "3.1.2",
            "type": "npm",
            "foundBy": "javascript-package-cataloger",
            "locations": [{"path": "/app/node_modules/bytes/package.json"}],
            "licenses": [{"value": "MIT"}],
            "language": "javascript",
            "cpes": ["cpe:2.3:a:bytes:bytes:3.1.2:*:*:*:*:node.js:*:*"],
            "purl": "pkg:npm/bytes@3.1.2",
            "metadata": {"name": "bytes", "version": "3.1.2"},
        },
        {
            "id": "pkg:npm/accepts@1.3.8",
            "name": "accepts",
            "version": "1.3.8",
            "type": "npm",
            "foundBy": "javascript-package-cataloger",
            "locations": [{"path": "/app/node_modules/accepts/package.json"}],
            "licenses": [{"value": "MIT"}],
            "language": "javascript",
            "cpes": ["cpe:2.3:a:accepts:accepts:1.3.8:*:*:*:*:node.js:*:*"],
            "purl": "pkg:npm/accepts@1.3.8",
            "metadata": {"name": "accepts", "version": "1.3.8"},
        },
        {
            "id": "pkg:npm/lodash@4.17.21",
            "name": "lodash",
            "version": "4.17.21",
            "type": "npm",
            "foundBy": "javascript-package-cataloger",
            "locations": [{"path": "/app/node_modules/lodash/package.json"}],
            "licenses": [{"value": "MIT"}],
            "language": "javascript",
            "cpes": ["cpe:2.3:a:lodash:lodash:4.17.21:*:*:*:*:node.js:*:*"],
            "purl": "pkg:npm/lodash@4.17.21",
            "metadata": {"name": "lodash", "version": "4.17.21"},
        },
    ],
    "artifactRelationships": [
        # express depends on body-parser: {parent: body-parser, child: express}
        # because "child depends on parent" in Syft's model
        {
            "parent": "pkg:npm/body-parser@1.20.1",
            "child": "pkg:npm/express@4.18.2",
            "type": "dependency-of",
        },
        # express depends on accepts
        {
            "parent": "pkg:npm/accepts@1.3.8",
            "child": "pkg:npm/express@4.18.2",
            "type": "dependency-of",
        },
        # body-parser depends on bytes
        {
            "parent": "pkg:npm/bytes@3.1.2",
            "child": "pkg:npm/body-parser@1.20.1",
            "type": "dependency-of",
        },
        # lodash has no dependencies (it's a root with no children pointing to it)
        # express and lodash are roots (nothing depends on them)
    ],
    "source": {
        "type": "image",
        "target": {
            "userInput": "myapp:latest",
            "imageID": "sha256:abc123def456",
            "manifestDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "tags": ["myapp:latest", "myapp:v1.0.0"],
            "repoDigests": [
                "myapp@sha256:0000000000000000000000000000000000000000000000000000000000000000"
            ],
            "digest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        },
    },
    "distro": {"name": "debian", "version": "12", "idLike": ["debian"]},
    "descriptor": {"name": "syft", "version": "1.0.0"},
    "schema": {
        "version": "16.0.0",
        "url": "https://raw.githubusercontent.com/anchore/syft/main/schema/json/schema-16.0.0.json",
    },
}


# Expected SyftPackage node IDs (same as normalized_id)
EXPECTED_SYFT_PACKAGES = {
    "npm|express|4.18.2",
    "npm|body-parser|1.20.1",
    "npm|bytes|3.1.2",
    "npm|accepts|1.3.8",
    "npm|lodash|4.17.21",
}

# Expected DEPENDS_ON relationships between SyftPackage nodes
# Direction: (dependent)-[:DEPENDS_ON]->(dependency)
EXPECTED_SYFT_PACKAGE_DEPENDENCIES = {
    ("npm|express|4.18.2", "npm|body-parser|1.20.1"),  # express needs body-parser
    ("npm|express|4.18.2", "npm|accepts|1.3.8"),  # express needs accepts
    ("npm|body-parser|1.20.1", "npm|bytes|3.1.2"),  # body-parser needs bytes
}


# Minimal valid Syft JSON for validation tests
SYFT_MINIMAL_VALID: dict[str, Any] = {
    "artifacts": [],
}


# Invalid Syft JSON samples for error testing
SYFT_INVALID_NO_ARTIFACTS = {"source": {"type": "image"}}


SYFT_INVALID_ARTIFACTS_NOT_LIST = {"artifacts": "not a list"}


SYFT_INVALID_RELATIONSHIPS_NOT_LIST = {
    "artifacts": [],
    "artifactRelationships": "not a list",
}
