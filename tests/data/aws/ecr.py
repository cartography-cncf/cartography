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
