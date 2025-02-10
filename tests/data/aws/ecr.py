import datetime


DESCRIBE_REPOSITORIES = {
    "repositories": [
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/example-repository",
            "registryId": "000000000000",
            "repositoryName": "example-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1/example-repository",
            "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/sample-repository",
            "registryId": "000000000000",
            "repositoryName": "sample-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1/sample-repository",
            "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
        {
            "repositoryArn": "arn:aws:ecr:us-east-1:000000000000:repository/test-repository",
            "registryId": "000000000000",
            "repositoryName": "test-repository",
            "repositoryUri": "000000000000.dkr.ecr.us-east-1/test-repository",
            "createdAt": datetime.datetime(2019, 1, 1, 0, 0, 1),
        },
    ],
}


LIST_REPOSITORY_IMAGES = {
    "000000000000.dkr.ecr.us-east-1/example-repository": [
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1",
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000001",
            "imageTag": "2",
        },
    ],
    "000000000000.dkr.ecr.us-east-1/sample-repository": [
        {
            # NOTE same digest and tag as image in example-repository
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1",
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000011",
            "imageTag": "2",
        },
    ],
    "000000000000.dkr.ecr.us-east-1/test-repository": [
        {
            # NOTE same digest but different tag from image in example-repository
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
            "imageTag": "1234567890",
        },
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000021",
            "imageTag": "1",
        },
        # Item without an imageDigest: will get filtered out and not ingested.
        {
            "imageTag": "1",
        },
        # Item without an imageTag
        {
            "imageDigest": "sha256:0000000000000000000000000000000000000000000000000000000000000031",
        },
    ],
}
