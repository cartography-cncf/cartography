from cartography.intel.aws.codebuild_supply_chain import (
    CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
)
from cartography.intel.aws.codebuild_supply_chain import (
    CODEBUILD_TAG_REVISION_CONFIDENCE,
)
from cartography.intel.aws.codebuild_supply_chain import match_images_to_builds
from cartography.intel.aws.codebuild_supply_chain import projects_with_linkable_source
from cartography.intel.aws.codebuild_supply_chain import transform_builds
from tests.data.aws.codebuild import FRONTEND_BUILD_UUID
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


def test_build_id_tag_matches_manifest_list_and_children():
    images = [
        {
            "digest": "sha256:list",
            "tags": [f"build-{FRONTEND_BUILD_UUID}", "latest"],
            "child_digests": ["sha256:amd64", "sha256:arm64"],
        },
    ]

    rows, evidenced = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert {row["image_digest"] for row in rows} == {
        "sha256:list",
        "sha256:amd64",
        "sha256:arm64",
    }
    assert rows[0] == {
        "image_digest": "sha256:list",
        "project_arn": FRONTEND_PROJECT_ARN,
        "build_id": f"frontend-build:{FRONTEND_BUILD_UUID}",
        "source_revision": FRONTEND_REVISION,
        "source_uri": FRONTEND_REPO,
        "source_provider": "github",
        "match_method": "codebuild_build_id_tag",
        "confidence": CODEBUILD_BUILD_ID_TAG_CONFIDENCE,
    }
    assert evidenced == {"sha256:list", "sha256:amd64", "sha256:arm64"}


def test_short_sha_tag_matches_revision():
    images = [{"digest": "sha256:a", "tags": [FRONTEND_PREVIOUS_REVISION[:7]]}]

    rows, _ = match_images_to_builds(images, transform_builds(GET_BUILDS))

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

    rows, evidenced = match_images_to_builds(images, builds)

    assert rows == []
    assert evidenced == {"sha256:a"}


def test_tags_naming_two_builds_are_ambiguous():
    images = [
        {
            "digest": "sha256:a",
            "tags": [
                f"build-{FRONTEND_BUILD_UUID}",
                f"build-{GET_BUILDS[1]['id'].split(':')[1]}",
            ],
        }
    ]

    rows, evidenced = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert rows == []
    assert evidenced == {"sha256:a"}


def test_unknown_build_id_falls_through_to_revision():
    images = [
        {
            "digest": "sha256:a",
            "tags": ["build-11111111-2222-4333-8444-555555555555", FRONTEND_REVISION],
        }
    ]

    rows, _ = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert [row["match_method"] for row in rows] == ["codebuild_tag_revision"]


def test_images_without_evidence_are_not_reevaluated():
    images = [{"digest": "sha256:a", "tags": ["latest", "deadbeefcafe"]}]

    rows, evidenced = match_images_to_builds(images, transform_builds(GET_BUILDS))

    assert rows == []
    assert evidenced == set()
