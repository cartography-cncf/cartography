from unittest.mock import MagicMock

import boto3
import pytest
from botocore.stub import Stubber

import tests.data.aws.ecr as test_data
from cartography.intel.aws.ecr import get_ecr_repository_images
from cartography.intel.aws.ecr import MANIFEST_LIST_MEDIA_TYPES

TEST_REGION = "us-east-1"
TEST_REPOSITORY = "example-repository"


def _untagged_image_details(digest: str) -> dict:
    return {
        "registryId": "000000000000",
        "repositoryName": TEST_REPOSITORY,
        "imageDigest": digest,
        "imageManifestMediaType": "application/vnd.oci.image.manifest.v1+json",
    }


AMD64_IMAGE_DETAILS = _untagged_image_details(test_data.MANIFEST_LIST_AMD64_DIGEST)
ARM64_IMAGE_DETAILS = _untagged_image_details(test_data.MANIFEST_LIST_ARM64_DIGEST)
ATTESTATION_IMAGE_DETAILS = _untagged_image_details(
    test_data.MANIFEST_LIST_ATTESTATION_DIGEST
)
STANDALONE_UNTAGGED_IMAGE_DETAILS = _untagged_image_details("sha256:" + "e" * 64)

# One more manifest list than a single batch_get_image call accepts.
MANY_MANIFEST_LIST_DIGESTS = [f"sha256:{n:064x}" for n in range(101)]
MANY_MANIFEST_LIST_DETAILS = [
    {**test_data.MULTI_ARCH_IMAGE_DETAILS, "imageDigest": digest}
    for digest in MANY_MANIFEST_LIST_DIGESTS
]
FIRST_100_MANIFEST_LIST_IDS = [
    {"imageDigest": digest} for digest in MANY_MANIFEST_LIST_DIGESTS[:100]
]
LAST_MANIFEST_LIST_ID = {"imageDigest": MANY_MANIFEST_LIST_DIGESTS[100]}


def _stubbed_session(client) -> MagicMock:
    boto3_session = MagicMock()
    boto3_session.client.return_value = client
    return boto3_session


def _ecr_client():
    return boto3.session.Session().client(
        "ecr",
        region_name=TEST_REGION,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )


def test_get_ecr_repository_images_fetches_all_manifest_lists_in_one_call():
    client = _ecr_client()
    stubber = Stubber(client)
    stubber.add_response(
        "describe_images",
        {
            "imageDetails": [
                test_data.MULTI_ARCH_IMAGE_DETAILS,
                AMD64_IMAGE_DETAILS,
                ARM64_IMAGE_DETAILS,
                ATTESTATION_IMAGE_DETAILS,
                test_data.SINGLE_PLATFORM_IMAGE_DETAILS,
                STANDALONE_UNTAGGED_IMAGE_DETAILS,
            ],
        },
        {"repositoryName": TEST_REPOSITORY, "maxResults": 1000},
    )
    stubber.add_response(
        "batch_get_image",
        test_data.BATCH_GET_MANIFEST_LIST_RESPONSE,
        {
            "repositoryName": TEST_REPOSITORY,
            "imageIds": [
                {"imageDigest": test_data.MANIFEST_LIST_DIGEST},
                {"imageDigest": test_data.SINGLE_PLATFORM_DIGEST},
            ],
            "acceptedMediaTypes": list(MANIFEST_LIST_MEDIA_TYPES),
        },
    )

    with stubber:
        images = get_ecr_repository_images(
            _stubbed_session(client), TEST_REGION, TEST_REPOSITORY
        )

    stubber.assert_no_pending_responses()
    multi_arch_details = {**test_data.MULTI_ARCH_IMAGE_DETAILS}
    multi_arch_details.pop("imageTags")
    single_platform_details = {**test_data.SINGLE_PLATFORM_IMAGE_DETAILS}
    single_platform_details.pop("imageTags")
    assert images == [
        {
            **multi_arch_details,
            "imageTag": "v1.0",
            "_manifest_images": [
                {
                    "digest": test_data.MANIFEST_LIST_AMD64_DIGEST,
                    "type": "image",
                    "architecture": "amd64",
                    "os": "linux",
                    "variant": None,
                    "attestation_type": None,
                    "attests_digest": None,
                    "media_type": "application/vnd.oci.image.manifest.v1+json",
                    "artifact_media_type": None,
                },
                {
                    "digest": test_data.MANIFEST_LIST_ARM64_DIGEST,
                    "type": "image",
                    "architecture": "arm64",
                    "os": "linux",
                    "variant": "v8",
                    "attestation_type": None,
                    "attests_digest": None,
                    "media_type": "application/vnd.oci.image.manifest.v1+json",
                    "artifact_media_type": None,
                },
                {
                    "digest": test_data.MANIFEST_LIST_ATTESTATION_DIGEST,
                    "type": "attestation",
                    "architecture": "unknown",
                    "os": "unknown",
                    "variant": None,
                    "attestation_type": "attestation-manifest",
                    "attests_digest": test_data.MANIFEST_LIST_AMD64_DIGEST,
                    "media_type": "application/vnd.oci.image.manifest.v1+json",
                    "artifact_media_type": None,
                },
            ],
        },
        {**single_platform_details, "imageTag": "latest"},
        STANDALONE_UNTAGGED_IMAGE_DETAILS,
    ]


def test_get_ecr_repository_images_requests_at_most_100_manifest_lists_per_call():
    client = _ecr_client()
    stubber = Stubber(client)
    stubber.add_response(
        "describe_images",
        {"imageDetails": MANY_MANIFEST_LIST_DETAILS},
        {"repositoryName": TEST_REPOSITORY, "maxResults": 1000},
    )
    stubber.add_response(
        "batch_get_image",
        {"images": []},
        {
            "repositoryName": TEST_REPOSITORY,
            "imageIds": FIRST_100_MANIFEST_LIST_IDS,
            "acceptedMediaTypes": list(MANIFEST_LIST_MEDIA_TYPES),
        },
    )
    stubber.add_response(
        "batch_get_image",
        {"images": []},
        {
            "repositoryName": TEST_REPOSITORY,
            "imageIds": [LAST_MANIFEST_LIST_ID],
            "acceptedMediaTypes": list(MANIFEST_LIST_MEDIA_TYPES),
        },
    )

    with stubber:
        images = get_ecr_repository_images(
            _stubbed_session(client), TEST_REGION, TEST_REPOSITORY
        )

    stubber.assert_no_pending_responses()
    assert len(images) == 101


@pytest.mark.parametrize("deleted_before", ["describe_images", "batch_get_image"])
def test_get_ecr_repository_images_skips_repository_deleted_mid_sync(deleted_before):
    client = _ecr_client()
    stubber = Stubber(client)
    describe_params = {"repositoryName": TEST_REPOSITORY, "maxResults": 1000}
    if deleted_before == "describe_images":
        stubber.add_client_error(
            "describe_images",
            service_error_code="RepositoryNotFoundException",
            expected_params=describe_params,
        )
    else:
        stubber.add_response(
            "describe_images",
            {
                "imageDetails": [
                    {
                        **_untagged_image_details(test_data.MANIFEST_LIST_DIGEST),
                        "imageManifestMediaType": "application/vnd.oci.image.index.v1+json",
                    }
                ]
            },
            describe_params,
        )
        stubber.add_client_error(
            "batch_get_image",
            service_error_code="RepositoryNotFoundException",
        )

    with stubber:
        images = get_ecr_repository_images(
            _stubbed_session(client), TEST_REGION, TEST_REPOSITORY
        )

    stubber.assert_no_pending_responses()
    assert images == []
