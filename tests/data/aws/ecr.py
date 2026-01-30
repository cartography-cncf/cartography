import datetime
import json

DESCRIBE_REPOSITORIES = {
    "repositories": [
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "registryId": "000000000000",
            "repositoryName": "example-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository",
            "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
            "registryId": "000000000000",
            "repositoryName": "sample-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository",
            "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
            "registryId": "000000000000",
            "repositoryName": "test-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository",
            "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}
DESCRIBE_IMAGES = {
    "imageDetails": {
        "registryId": "000000000000",
        "imageSizeInBytes": 1024,
        "imagePushedAt": "2025-01-01T00:00:00.000000-00:00",
        "imageScanStatus": {
            "status": "COMPLETE",
            "description": "The scan was completed successfully.",
        },
        "imageScanFindingsSummary": {
            "imageScanCompletedAt": "2025-01-01T00:00:00-00:00",
            "vulnerabilitySourceUpdatedAt": "2025-01-01T00:00:00-00:00",
            "findingSeverityCounts": {
                "CRITICAL": 1,
                "HIGH": 1,
                "MEDIUM": 1,
                "INFORMATIONAL": 1,
                "LOW": 1,
            },
        },
        "imageManifestMediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "artifactMediaType": "application/vnd.docker.container.image.v1+json",
        "lastRecordedPullTime": "2025-01-01T01:01:01.000000-00:00",
    },
}

LIST_REPOSITORY_IMAGES = {
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/example-repository": [
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1",
            "repositoryName": "example-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "latest",
            "repositoryName": "example-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000001",
            "imageTag": "2",
            "repositoryName": "example-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
    ],
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/sample-repository": [
        {
            # NOTE same digest and tag as image in example-repository
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1",
            "repositoryName": "sample-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000011",
            "imageTag": "2",
            "repositoryName": "sample-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
    ],
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/test-repository": [
        {
            # NOTE same digest but different tag from image in example-repository
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1234567890",
            "repositoryName": "test-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000021",
            "imageTag": "1",
            "repositoryName": "test-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
        # Item without an imageDigest: will get filtered out and not ingested.
        {
            "imageTag": "1",
            "repositoryName": "test-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
        # Item without an imageTag
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000031",
            "repositoryName": "test-repository",
            **DESCRIBE_IMAGES["imageDetails"],
        },
    ],
}

# Sample Docker manifest for testing
SAMPLE_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
        "mediaType": "application/vnd.docker.container.image.v1+json",
        "size": 7023,
        "digest": "sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f0c7a0b0c91",
    },
    "layers": [
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 977,
            "digest": "sha256:e692418e3dfaf5b2d8b94d14cb0c9e5b5c28e45a5f8df7b7e4e1d094c4e1b3e0",
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 1024,
            "digest": "sha256:3c3a4604a545cdc127456d94e421cd355bca5b528f4a9c1905b15da2eb4a4c6b",
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 2048,
            "digest": "sha256:ec4b8955958665577945c89419d1af06b5f7636b4ac3da7f12184802ad867736",
        },
    ],
}

# Sample config blob with diff_ids for testing
SAMPLE_CONFIG_BLOB = {
    "architecture": "amd64",
    "os": "linux",
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
            "sha256:fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9",
            "sha256:4ac5bb3f45ba451e817df5f30b950f6eb32145e00ba5f134973810881fde7ac0",
        ],
    },
}

# Multi-arch manifest list for testing
SAMPLE_MANIFEST_LIST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "manifests": [
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 1024,
            "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1",
            "platform": {"architecture": "amd64", "os": "linux"},
        },
        {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "size": 1024,
            "digest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2",
            "platform": {"architecture": "arm64", "os": "linux", "variant": "v8"},
        },
    ],
}

# Response for batch_get_image API
BATCH_GET_IMAGE_RESPONSE = {
    "images": [
        {
            "imageManifest": json.dumps(SAMPLE_MANIFEST),
            "imageManifestMediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "imageId": {
                "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
                "imageTag": "1",
            },
            "registryId": "000000000000",
            "repositoryName": "example-repository",
        }
    ]
}

# Response for get_download_url_for_layer API
GET_DOWNLOAD_URL_RESPONSE = {
    "downloadUrl": "https://example.s3.amazonaws.com/layer?X-Amz-Algorithm=AWS4-HMAC-SHA256...",
    "layerDigest": "sha256:b5b2b2c507a0944348e0303114d8d93aaaa081732b86451d9bce1f0c7a0b0c91",
}

# Attestation image manifest (in-toto format) - should be filtered
ATTESTATION_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {
        "mediaType": "application/vnd.in-toto+json",
        "digest": "sha256:3a5a1d9c5f5b4e7e8f9d1c2b3a4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d",
        "size": 1582,
    },
    "layers": [
        {
            "mediaType": "application/vnd.in-toto+json",
            "digest": "sha256:a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
            "size": 13268,
        }
    ],
}

# SLSA provenance blob (in-toto attestation payload)
SLSA_PROVENANCE_BLOB = {
    "predicate": {
        "materials": [
            {
                "uri": "pkg:docker/000000000000.dkr.ecr.us-east-1.amazonaws.com/base-image@sha256:parent123",
                "digest": {
                    "sha256": "parent1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
                },
            }
        ]
    }
}

# Multi-layer container image manifest
MULTI_LAYER_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
    "config": {
        "mediaType": "application/vnd.docker.container.image.v1+json",
        "size": 9276,
        "digest": "sha256:5e3e8642f7c9a07c6e3c1df7e71d9a5f08d8bb8d99f4c7a1e8f9a0b1c2d3e4f5",
    },
    "layers": [
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 3370706,
            "digest": "sha256:layer1digest0000000000000000000000000000000000000000000000000001",
        },
        {
            "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
            "size": 1234567,
            "digest": "sha256:layer2digest0000000000000000000000000000000000000000000000000002",
        },
    ],
}

# Config blob for multi-layer container
MULTI_LAYER_CONFIG = {
    "architecture": "amd64",
    "os": "linux",
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "sha256:3333333333333333333333333333333333333333333333333333333333333333",
            "sha256:4444444444444444444444444444444444444444444444444444444444444444",
            "sha256:5555555555555555555555555555555555555555555555555555555555555555",
            "sha256:6666666666666666666666666666666666666666666666666666666666666666",
            "sha256:7777777777777777777777777777777777777777777777777777777777777777",
            "sha256:8888888888888888888888888888888888888888888888888888888888888888",
            "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        ],
    },
    "config": {
        "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
        "Cmd": ["/bin/sh"],
    },
}

# BuildKit cache manifest (should be filtered out)
BUILDKIT_CACHE_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {
        "mediaType": "application/vnd.buildkit.cacheconfig.v0",
        "digest": "sha256:buildkit0000000000000000000000000000000000000000000000000000001",
        "size": 573,
    },
    "layers": [
        {
            "mediaType": "application/vnd.buildkit.cache.v0",
            "digest": "sha256:cachelayer00000000000000000000000000000000000000000000000000001",
            "size": 1024,
        }
    ],
}


# Multi-arch fixtures shaped like AWS CLI responses
MULTI_ARCH_INDEX = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.index.v1+json",
    "manifests": [
        {
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "size": 2198,
            "platform": {"architecture": "amd64", "os": "linux"},
        },
        {
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "digest": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
            "size": 2198,
            "platform": {"architecture": "arm64", "os": "linux", "variant": "v8"},
        },
        {
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "digest": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
            "size": 566,
            "annotations": {
                "vnd.docker.reference.type": "attestation-manifest",
                "vnd.docker.reference.digest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            },
            "platform": {"architecture": "unknown", "os": "unknown"},
        },
    ],
}

MULTI_ARCH_AMD64_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "digest": "sha256:aaaabbbbccccddddeeeeffff0000111122223333444455556666777788889999",
        "size": 7404,
    },
    "layers": [
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "digest": "sha256:layeramd640000000000000000000000000000000000000000000000000000001",
            "size": 28227259,
        }
    ],
}

MULTI_ARCH_ARM64_MANIFEST = {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": {
        "mediaType": "application/vnd.oci.image.config.v1+json",
        "digest": "sha256:9999888877776666555544443333222211110000fffedddcccbbbbaaa9998888",
        "size": 7403,
    },
    "layers": [
        {
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "digest": "sha256:layerarm640000000000000000000000000000000000000000000000000000001",
            "size": 28066320,
        }
    ],
}

MULTI_ARCH_AMD64_CONFIG = {
    "architecture": "amd64",
    "os": "linux",
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:diffamd6400000000000000000000000000000000000000000000000000000001",
            "sha256:diffamd6400000000000000000000000000000000000000000000000000000002",
        ],
    },
}

MULTI_ARCH_ARM64_CONFIG = {
    "architecture": "arm64",
    "os": "linux",
    "variant": "v8",
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:diffarm6400000000000000000000000000000000000000000000000000000001",
        ],
    },
}

MANIFEST_LIST_DIGEST = (
    "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
)
MANIFEST_LIST_AMD64_DIGEST = (
    "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
)
MANIFEST_LIST_ARM64_DIGEST = (
    "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
)
MANIFEST_LIST_ATTESTATION_DIGEST = (
    "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
)

# Mock response for batch_get_image when fetching manifest list
BATCH_GET_MANIFEST_LIST_RESPONSE = {
    "images": [
        {
            "imageManifest": json.dumps(MULTI_ARCH_INDEX),
            "imageManifestMediaType": "application/vnd.oci.image.index.v1+json",
            "imageId": {
                "imageDigest": MANIFEST_LIST_DIGEST,
            },
            "registryId": "000000000000",
            "repositoryName": "multi-arch-repository",
        }
    ]
}

# Image details for a multi-arch manifest list
MULTI_ARCH_IMAGE_DETAILS = {
    "registryId": "000000000000",
    "repositoryName": "multi-arch-repository",
    "imageDigest": MANIFEST_LIST_DIGEST,
    "imageTags": ["v1.0"],
    "imageSizeInBytes": 50000000,
    "imagePushedAt": "2025-01-01T00:00:00.000000-00:00",
    "imageManifestMediaType": "application/vnd.oci.image.index.v1+json",
    "lastRecordedPullTime": "2025-01-01T01:01:01.000000-00:00",
}

# Single-platform image incorrectly marked as manifest list (bug scenario)
SINGLE_PLATFORM_DIGEST = (
    "sha256:914758fa1c15b12c7dfa8cab15eb53b7bbb5143386911da492b00c73c49eef6f"
)

SINGLE_PLATFORM_IMAGE_DETAILS = {
    "registryId": "000000000000",
    "repositoryName": "single-platform-repository",
    "imageDigest": SINGLE_PLATFORM_DIGEST,
    "imageTags": ["latest"],
    "imageSizeInBytes": 12345678,
    "imagePushedAt": "2025-01-01T00:00:00.000000-00:00",
    # AWS ECR sometimes reports manifest list media type even for single-platform images
    "imageManifestMediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
    "lastRecordedPullTime": "2025-01-01T01:01:01.000000-00:00",
}

# Empty response when trying to fetch as manifest list (the bug scenario)
BATCH_GET_MANIFEST_LIST_EMPTY_RESPONSE: dict[str, list] = {"images": []}
