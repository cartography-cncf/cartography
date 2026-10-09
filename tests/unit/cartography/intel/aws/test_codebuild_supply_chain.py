from unittest.mock import MagicMock

import botocore.exceptions

from cartography.intel.aws import codebuild_supply_chain
from cartography.intel.aws.codebuild_supply_chain import (
    CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
)
from cartography.intel.aws.codebuild_supply_chain import (
    CODEBUILD_TAG_REVISION_CONFIDENCE,
)
from cartography.intel.aws.codebuild_supply_chain import get_builds
from cartography.intel.aws.codebuild_supply_chain import group_tags_by_digest
from cartography.intel.aws.codebuild_supply_chain import match_images_to_builds
from cartography.intel.aws.codebuild_supply_chain import MAX_RECENT_BUILDS_PER_PROJECT
from cartography.intel.aws.codebuild_supply_chain import projects_with_linkable_source
from cartography.intel.aws.codebuild_supply_chain import select_build_ids
from cartography.intel.aws.codebuild_supply_chain import tagged_build_uuids
from cartography.intel.aws.codebuild_supply_chain import transform_builds
from tests.data.aws.codebuild import FRONTEND_BUILD_UUID
from tests.data.aws.codebuild import FRONTEND_PREVIOUS_BUILD_UUID
from tests.data.aws.codebuild import FRONTEND_PREVIOUS_REVISION
from tests.data.aws.codebuild import FRONTEND_REVISION
from tests.data.aws.codebuild import GET_BUILDS
from tests.data.aws.codebuild import GET_PROJECTS

FRONTEND_PROJECT_ARN = "arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build"
FRONTEND_REPO = "https://github.com/example/frontend"


def _build(project: str, uuid: str, revision: str, location: str) -> dict:
    return {
        "id": f"{project}:{uuid}",
        "arn": f"arn:aws:codebuild:eu-west-1:123456789012:build/{project}:{uuid}",
        "resolvedSourceVersion": revision,
        "source": {"type": "GITHUB", "location": location},
    }


def test_projects_with_linkable_source_skips_codecommit():
    assert projects_with_linkable_source(GET_PROJECTS) == ["frontend-build"]


def test_group_tags_by_digest():
    ecr_images = {
        ("eu-west-1", "Latest", "repo:latest", "repo", "sha256:a"),
        ("eu-west-1", f"build-{FRONTEND_BUILD_UUID}", "repo:b", "repo", "sha256:a"),
        ("eu-west-1", None, "repo@sha256:b", "repo", "sha256:b"),
    }

    images = group_tags_by_digest(ecr_images)

    assert images == [
        {"digest": "sha256:a", "tags": [f"build-{FRONTEND_BUILD_UUID}", "latest"]},
    ]
    assert tagged_build_uuids(images) == {FRONTEND_BUILD_UUID}


def test_select_build_ids_keeps_recent_and_tagged_older_builds():
    listed = [
        f"frontend-build:00000000-0000-4000-8000-{i:012d}"
        for i in range(MAX_RECENT_BUILDS_PER_PROJECT)
    ] + [
        f"frontend-build:{FRONTEND_PREVIOUS_BUILD_UUID}",
        "frontend-build:11111111-2222-4333-8444-555555555555",
    ]

    selected = select_build_ids(listed, {FRONTEND_PREVIOUS_BUILD_UUID})

    assert selected == listed[:MAX_RECENT_BUILDS_PER_PROJECT] + [
        f"frontend-build:{FRONTEND_PREVIOUS_BUILD_UUID}"
    ]


def test_transform_builds():
    builds = transform_builds(GET_BUILDS)

    assert builds[0] == {
        "build_id": f"frontend-build:{FRONTEND_BUILD_UUID}",
        "build_uuid": FRONTEND_BUILD_UUID,
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
            _build(
                "frontend-build",
                FRONTEND_BUILD_UUID,
                "refs/heads/main",
                "https://github.com/example/frontend.git",
            ),
        ]
    )

    assert len(builds) == 1
    assert builds[0]["source_revision"] is None


def test_build_id_tag_matches_build():
    images = [
        {"digest": "sha256:list", "tags": [f"build-{FRONTEND_BUILD_UUID}", "latest"]},
    ]

    rows = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert rows == [
        {
            "image_digest": "sha256:list",
            "project_arn": FRONTEND_PROJECT_ARN,
            "build_id": f"frontend-build:{FRONTEND_BUILD_UUID}",
            "source_revision": FRONTEND_REVISION,
            "source_uri": FRONTEND_REPO,
            "source_provider": "github",
            "match_method": "codebuild_build_id_tag",
            "confidence": CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
        }
    ]


def test_short_sha_tag_matches_revision():
    images = [{"digest": "sha256:a", "tags": [FRONTEND_PREVIOUS_REVISION[:7]]}]

    rows = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert rows == [
        {
            "image_digest": "sha256:a",
            "project_arn": FRONTEND_PROJECT_ARN,
            "build_id": None,
            "source_revision": FRONTEND_PREVIOUS_REVISION,
            "source_uri": FRONTEND_REPO,
            "source_provider": "github",
            "match_method": "codebuild_tag_revision",
            "confidence": CODEBUILD_TAG_REVISION_CONFIDENCE,
        }
    ]


def test_revision_built_by_two_projects_is_ambiguous():
    builds = transform_builds(
        [
            *GET_BUILDS,
            _build(
                "frontend-build-staging",
                "c2d3e4f5-a6b7-4c8d-9e0f-1a2b3c4d5e6f",
                FRONTEND_REVISION,
                "https://github.com/example/frontend.git",
            ),
        ]
    )
    images = [{"digest": "sha256:a", "tags": [FRONTEND_REVISION]}]

    assert match_images_to_builds(images, builds) == []


def test_tags_naming_two_builds_are_ambiguous():
    images = [
        {
            "digest": "sha256:a",
            "tags": [
                f"build-{FRONTEND_BUILD_UUID}",
                f"build-{FRONTEND_PREVIOUS_BUILD_UUID}",
            ],
        }
    ]

    assert match_images_to_builds(images, transform_builds(GET_BUILDS)) == []


def test_unknown_build_id_falls_through_to_revision():
    images = [
        {
            "digest": "sha256:a",
            "tags": ["build-11111111-2222-4333-8444-555555555555", FRONTEND_REVISION],
        }
    ]

    rows = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert [row["match_method"] for row in rows] == ["codebuild_tag_revision"]


def test_revision_matching_off_keeps_build_id_matches_only():
    images = [
        {"digest": "sha256:a", "tags": [f"build-{FRONTEND_BUILD_UUID}"]},
        {"digest": "sha256:b", "tags": [FRONTEND_PREVIOUS_REVISION]},
    ]

    rows = match_images_to_builds(
        images, transform_builds(GET_BUILDS), match_revisions=False
    )

    assert [(row["image_digest"], row["match_method"]) for row in rows] == [
        ("sha256:a", "codebuild_build_id_tag"),
    ]


def _client_listing(paginate_side_effect) -> MagicMock:
    client = MagicMock()
    client.get_paginator.return_value.paginate.side_effect = paginate_side_effect
    return client


def test_get_builds_reports_unreadable_region(mocker):
    client = _client_listing(
        botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "denied"}},
            "ListBuildsForProject",
        )
    )
    mocker.patch.object(
        codebuild_supply_chain, "create_boto3_client", return_value=client
    )

    assert get_builds(MagicMock(), "eu-west-1", ["frontend-build"], set()) is None


def test_get_builds_returns_empty_list_for_region_without_builds(mocker):
    client = _client_listing(lambda **_: iter([{"ids": []}]))
    mocker.patch.object(
        codebuild_supply_chain, "create_boto3_client", return_value=client
    )

    assert get_builds(MagicMock(), "eu-west-1", ["frontend-build"], set()) == []
