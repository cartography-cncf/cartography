import datetime


DESCRIBE_REPOSITORIES = {
    'repositories': [
        {
            'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/example-repository',
            'registryId': '000000000000',
            'repositoryName': 'example-repository',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/example-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/sample-repository',
            'registryId': '000000000000',
            'repositoryName': 'sample-repository',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/sample-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            'repositoryArn': 'arn:aws:ecr:us-east-1:000000000000:repository/test-repository',
            'registryId': '000000000000',
            'repositoryName': 'test-repository',
            'repositoryUri': '000000000000.dkr.ecr.us-east-1/test-repository',
            'createdAt': datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}
DESCRIBE_IMAGES = {
    'imageDetails':
    {
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
    '000000000000.dkr.ecr.us-east-1/example-repository': [
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'imageTag': '1',
            'repositoryName': 'example-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000001',
            'imageTag': '2',
            'repositoryName': 'example-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
    ],
    '000000000000.dkr.ecr.us-east-1/sample-repository': [
        {
            # NOTE same digest and tag as image in example-repository
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'imageTag': '1',
            'repositoryName': 'sample-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000011',
            'imageTag': '2',
            'repositoryName': 'sample-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
    ],
    '000000000000.dkr.ecr.us-east-1/test-repository': [
        {
            # NOTE same digest but different tag from image in example-repository
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000000',
            'imageTag': '1234567890',
            'repositoryName': 'test-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000021',
            'imageTag': '1',
            'repositoryName': 'test-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
        # Item without an imageDigest: will get filtered out and not ingested.
        {
            'imageTag': '1',
            'repositoryName': 'test-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
        # Item without an imageTag
        {
            'imageDigest': 'sha256:0000000000000000000000000000000000000000000000000000000000000031',
            'repositoryName': 'test-repository',
            **DESCRIBE_IMAGES['imageDetails'],
        },
    ],
}
