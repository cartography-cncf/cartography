from unittest.mock import MagicMock

import botocore.exceptions

from cartography.intel.aws import codebuild_supply_chain
from cartography.intel.aws.codebuild_supply_chain import build_ids_by_region
from cartography.intel.aws.codebuild_supply_chain import candidate_build_ids
from cartography.intel.aws.codebuild_supply_chain import (
    CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
)
from cartography.intel.aws.codebuild_supply_chain import get_builds
from cartography.intel.aws.codebuild_supply_chain import linkable_source
from cartography.intel.aws.codebuild_supply_chain import match_images_to_builds
from cartography.intel.aws.codebuild_supply_chain import transform_builds
from tests.data.aws.codebuild import FRONTEND_BUILD_UUID
from tests.data.aws.codebuild import FRONTEND_PREVIOUS_BUILD_UUID
from tests.data.aws.codebuild import FRONTEND_REVISION
from tests.data.aws.codebuild import GET_BUILDS

FRONTEND_PROJECT_ARN = "arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build"
FRONTEND_REPO = "https://github.com/example/frontend"
FRONTEND_BUILD_ID = f"frontend-build:{FRONTEND_BUILD_UUID}"


def test_linkable_source():
    assert linkable_source(
        {"type": "GITHUB", "location": "https://github.com/example/frontend.git"}
    ) == ("github", FRONTEND_REPO)
    assert linkable_source({"type": "CODECOMMIT", "location": "https://x"}) is None


def test_candidate_build_ids_pairs_uuid_tags_with_project_named_repository():
    ecr_images = {
        (
            "eu-west-1",
            f"build-{FRONTEND_BUILD_UUID}",
            "u1",
            "frontend-build",
            "sha256:a",
        ),
        ("eu-west-1", "latest", "u2", "frontend-build", "sha256:a"),
        ("eu-west-1", None, "u3", "frontend-build", "sha256:b"),
        # No CodeBuild project shares this repository's name.
        (
            "eu-west-1",
            f"build-{FRONTEND_BUILD_UUID}",
            "u4",
            "team/frontend",
            "sha256:c",
        ),
    }

    assert candidate_build_ids(ecr_images, {"frontend-build"}) == {
        FRONTEND_BUILD_ID: {"sha256:a"},
    }


def test_build_ids_are_looked_up_where_the_project_lives():
    routed = build_ids_by_region(
        {FRONTEND_BUILD_ID, "backend-deploy:0b6a1f3c-5d2e-4f7a-9c8b-1d2e3f4a5b6c"},
        {
            "us-east-1": {"frontend-build"},
            "eu-west-1": {"frontend-build", "backend-deploy"},
            "ap-south-1": {"unrelated"},
        },
    )

    assert routed == {
        "eu-west-1": [
            "backend-deploy:0b6a1f3c-5d2e-4f7a-9c8b-1d2e3f4a5b6c",
            FRONTEND_BUILD_ID,
        ],
        "us-east-1": [FRONTEND_BUILD_ID],
    }


def test_transform_builds():
    assert transform_builds(GET_BUILDS)[0] == {
        "build_id": FRONTEND_BUILD_ID,
        "project_arn": FRONTEND_PROJECT_ARN,
        "source_revision": FRONTEND_REVISION,
        "source_uri": FRONTEND_REPO,
        "source_provider": "github",
    }


def test_transform_builds_skips_unlinkable_sources_and_non_sha_revisions():
    builds = transform_builds(
        [
            {
                "id": "backend-deploy:0b6a1f3c-5d2e-4f7a-9c8b-1d2e3f4a5b6c",
                "arn": "arn:aws:codebuild:eu-west-1:123456789012:build/backend-deploy:0b6a1f3c-5d2e-4f7a-9c8b-1d2e3f4a5b6c",
                "source": {"type": "CODECOMMIT", "location": "https://example"},
            },
            {**GET_BUILDS[0], "resolvedSourceVersion": "refs/heads/main"},
        ]
    )

    assert len(builds) == 1
    assert builds[0]["source_revision"] is None


def test_match_images_to_builds():
    rows = match_images_to_builds(
        {FRONTEND_BUILD_ID: {"sha256:a"}}, transform_builds(GET_BUILDS)
    )

    assert rows == [
        {
            "image_digest": "sha256:a",
            "build_id": FRONTEND_BUILD_ID,
            "project_arn": FRONTEND_PROJECT_ARN,
            "source_revision": FRONTEND_REVISION,
            "source_uri": FRONTEND_REPO,
            "source_provider": "github",
            "match_method": "codebuild_build_id_tag",
            "confidence": CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
        }
    ]


def test_image_tagged_with_two_builds_is_ambiguous():
    candidates = {
        FRONTEND_BUILD_ID: {"sha256:a"},
        f"frontend-build:{FRONTEND_PREVIOUS_BUILD_UUID}": {"sha256:a"},
    }

    assert match_images_to_builds(candidates, transform_builds(GET_BUILDS)) == []


def test_get_builds_reports_unreadable_region(mocker):
    client = MagicMock()
    client.batch_get_builds.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
        "BatchGetBuilds",
    )
    mocker.patch.object(
        codebuild_supply_chain, "create_boto3_client", return_value=client
    )

    assert get_builds(MagicMock(), "eu-west-1", [FRONTEND_BUILD_ID]) is None


def test_get_builds_returns_empty_list_when_no_build_is_found(mocker):
    client = MagicMock()
    client.batch_get_builds.return_value = {
        "builds": [],
        "buildsNotFound": [FRONTEND_BUILD_ID],
    }
    mocker.patch.object(
        codebuild_supply_chain, "create_boto3_client", return_value=client
    )

    assert get_builds(MagicMock(), "eu-west-1", [FRONTEND_BUILD_ID]) == []
