"""Fixture payloads for the GHCR (packages + container registry) sync tests."""

from copy import deepcopy

GET_CONTAINER_PACKAGES = [
    {
        "id": 1001,
        "name": "api",
        "package_type": "container",
        "owner": {"login": "simpsoncorp"},
        "version_count": 2,
        "visibility": "private",
        "url": "https://api.github.com/orgs/simpsoncorp/packages/container/api",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-04-01T00:00:00Z",
        "html_url": "https://github.com/orgs/simpsoncorp/packages/container/package/api",
        "repository": {
            "id": 1,
            "html_url": "https://github.com/simpsoncorp/sample_repo",
        },
    },
    {
        "id": 1002,
        "name": "worker",
        "package_type": "container",
        "owner": {"login": "simpsoncorp"},
        "version_count": 1,
        "visibility": "internal",
        "url": "https://api.github.com/orgs/simpsoncorp/packages/container/worker",
        "created_at": "2025-02-01T00:00:00Z",
        "updated_at": "2025-04-15T00:00:00Z",
        "html_url": "https://github.com/orgs/simpsoncorp/packages/container/package/worker",
        "repository": None,
    },
]

# Two versions for "api": one single-image manifest, one multi-arch manifest list.
# One version for "worker": single image, no source attestation.
DIGEST_API_LATEST = (
    "sha256:1111111111111111111111111111111111111111111111111111111111111111"
)
DIGEST_API_INDEX = (
    "sha256:2222222222222222222222222222222222222222222222222222222222222222"
)
DIGEST_API_AMD64 = (
    "sha256:3333333333333333333333333333333333333333333333333333333333333333"
)
DIGEST_API_ARM64 = (
    "sha256:4444444444444444444444444444444444444444444444444444444444444444"
)
DIGEST_WORKER = (
    "sha256:5555555555555555555555555555555555555555555555555555555555555555"
)

LAYER_DIFF_A = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
LAYER_DIFF_B = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
LAYER_DIFF_C = "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

PACKAGE_VERSIONS_BY_NAME = {
    "api": [
        {
            "id": 11,
            "name": DIGEST_API_LATEST,
            "url": "...",
            "package_html_url": "...",
            "created_at": "2025-04-01T10:00:00Z",
            "updated_at": "2025-04-01T10:00:00Z",
            "metadata": {
                "package_type": "container",
                "container": {"tags": ["latest", "v1.0.0"]},
            },
        },
        {
            "id": 12,
            "name": DIGEST_API_INDEX,
            "url": "...",
            "created_at": "2025-04-10T10:00:00Z",
            "updated_at": "2025-04-10T10:00:00Z",
            "metadata": {
                "package_type": "container",
                "container": {"tags": ["v1.1.0"]},
            },
        },
    ],
    "worker": [
        {
            "id": 21,
            "name": DIGEST_WORKER,
            "url": "...",
            "created_at": "2025-04-15T08:00:00Z",
            "updated_at": "2025-04-15T08:00:00Z",
            "metadata": {
                "package_type": "container",
                "container": {"tags": ["latest"]},
            },
        },
    ],
}


def _config(layers, arch="amd64", os_name="linux", history=None):
    return {
        "architecture": arch,
        "os": os_name,
        "rootfs": {"type": "layers", "diff_ids": layers},
        "history": history
        or [{"created_by": f"COPY layer-{i}"} for i in range(len(layers))],
    }


def _manifest(layers, config_digest):
    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "digest": config_digest,
            "size": 1234,
        },
        "layers": [
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": f"sha256:layer-blob-{i}",
                "size": 1024,
            }
            for i, _ in enumerate(layers)
        ],
    }


CONFIG_BLOB_API_AMD64 = _config([LAYER_DIFF_A, LAYER_DIFF_B])
CONFIG_BLOB_API_ARM64 = _config([LAYER_DIFF_A, LAYER_DIFF_C], arch="arm64")
CONFIG_BLOB_WORKER = _config([LAYER_DIFF_C])

MANIFEST_API_LATEST = _manifest([LAYER_DIFF_A, LAYER_DIFF_B], "sha256:cfg-api-amd64")
MANIFEST_API_AMD64 = _manifest([LAYER_DIFF_A, LAYER_DIFF_B], "sha256:cfg-api-amd64")
MANIFEST_API_ARM64 = _manifest([LAYER_DIFF_A, LAYER_DIFF_C], "sha256:cfg-api-arm64")
MANIFEST_WORKER = _manifest([LAYER_DIFF_C], "sha256:cfg-worker")

MANIFEST_API_INDEX = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.index.v1+json",
    "manifests": [
        {
            "digest": DIGEST_API_AMD64,
            "platform": {"architecture": "amd64", "os": "linux"},
        },
        {
            "digest": DIGEST_API_ARM64,
            "platform": {"architecture": "arm64", "os": "linux"},
        },
    ],
}


MANIFESTS_BY_REFERENCE = {
    ("simpsoncorp/api", DIGEST_API_LATEST): deepcopy(MANIFEST_API_LATEST),
    ("simpsoncorp/api", DIGEST_API_INDEX): deepcopy(MANIFEST_API_INDEX),
    ("simpsoncorp/api", DIGEST_API_AMD64): deepcopy(MANIFEST_API_AMD64),
    ("simpsoncorp/api", DIGEST_API_ARM64): deepcopy(MANIFEST_API_ARM64),
    ("simpsoncorp/worker", DIGEST_WORKER): deepcopy(MANIFEST_WORKER),
}

CONFIG_BLOBS_BY_DIGEST = {
    "sha256:cfg-api-amd64": deepcopy(CONFIG_BLOB_API_AMD64),
    "sha256:cfg-api-arm64": deepcopy(CONFIG_BLOB_API_ARM64),
    "sha256:cfg-worker": deepcopy(CONFIG_BLOB_WORKER),
}

# A SLSA v1 in-toto statement for DIGEST_API_LATEST. The DSSE payload is
# base64-encoded JSON; we keep it as a Python dict here and encode in tests.
SLSA_STATEMENT_API_LATEST = {
    "_type": "https://in-toto.io/Statement/v1",
    "subject": [
        {
            "name": "ghcr.io/simpsoncorp/api",
            "digest": {"sha256": DIGEST_API_LATEST.split(":")[1]},
        }
    ],
    "predicateType": "https://slsa.dev/provenance/v1",
    "predicate": {
        "buildDefinition": {
            "buildType": "https://actions.github.io/buildtypes/workflow/v1",
            "externalParameters": {
                "workflow": {
                    "ref": "refs/heads/main",
                    "repository": "https://github.com/simpsoncorp/sample_repo",
                    "path": ".github/workflows/build.yml",
                },
            },
            "resolvedDependencies": [
                {
                    "uri": "git+https://github.com/simpsoncorp/sample_repo@refs/heads/main",
                    "digest": {"gitCommit": "abc123def456abc123def456abc123def4567890"},
                },
            ],
        },
        "runDetails": {"builder": {"id": "https://github.com/actions/runner/v2"}},
    },
}
