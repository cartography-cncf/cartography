from unittest.mock import MagicMock

import cartography.intel.aws.codebuild
import cartography.intel.aws.codebuild_supply_chain
from cartography.analysis.ontology.analysis import CODEBUILD_IMAGE_PACKAGED_FROM
from cartography.intel.aws.codebuild import sync
from cartography.util import run_typed_analysis_job
from tests.data.aws.codebuild import FRONTEND_BUILD_UUID
from tests.data.aws.codebuild import FRONTEND_PREVIOUS_REVISION
from tests.data.aws.codebuild import FRONTEND_REVISION
from tests.data.aws.codebuild import GET_BUILDS
from tests.data.aws.codebuild import GET_PROJECTS
from tests.integration.cartography.intel.aws.common import create_test_account
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_ACCOUNT_ID = "000000000000"
TEST_REGION = "eu-west-1"
TEST_UPDATE_TAG = 123456789


def test_sync_cloudwatch(mocker, neo4j_session):
    # Arrange
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = [TEST_REGION]
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    mocker.patch.object(
        cartography.intel.aws.codebuild,
        "get_all_codebuild_projects",
        return_value=GET_PROJECTS,
    )
    mocker.patch.object(
        cartography.intel.aws.codebuild_supply_chain,
        "get_builds",
        return_value=[],
    )

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID},
    )

    # Assert
    assert check_nodes(neo4j_session, "AWSCodeBuildProject", ["arn"]) == {
        ("arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build",),
        ("arn:aws:codebuild:eu-west-1:123456789012:project/backend-deploy",),
    }

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSAccount",
        "id",
        "AWSCodeBuildProject",
        "arn",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (
            TEST_ACCOUNT_ID,
            "arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build",
        ),
        (
            TEST_ACCOUNT_ID,
            "arn:aws:codebuild:eu-west-1:123456789012:project/backend-deploy",
        ),
    }


FRONTEND_PROJECT_ARN = "arn:aws:codebuild:eu-west-1:123456789012:project/frontend-build"
FRONTEND_REPO = "https://github.com/example/frontend"


def _create_ecr_images(neo4j_session):
    neo4j_session.run(
        """
        MATCH (account:AWSAccount {id: $account_id})
        MERGE (account)-[:RESOURCE]->(repo:AWSECRRepository {id: 'frontend-repo'})
        SET repo.region = $region
        WITH repo
        UNWIND $images AS image
        MERGE (img:AWSECRImage:Image {id: image.digest})
        SET img.digest = image.digest
        MERGE (repo)-[:REPO_IMAGE]->(repo_img:AWSECRRepositoryImage {id: image.uri})
        SET repo_img.tag = image.tag
        MERGE (repo_img)-[:IMAGE]->(img)
        """,
        account_id=TEST_ACCOUNT_ID,
        region=TEST_REGION,
        images=[
            {
                "digest": "sha256:build-id-tagged",
                "uri": "frontend:build-id",
                "tag": f"build-{FRONTEND_BUILD_UUID}",
            },
            {
                "digest": "sha256:revision-tagged",
                "uri": "frontend:revision",
                "tag": FRONTEND_PREVIOUS_REVISION[:7],
            },
            {
                "digest": "sha256:provenance-matched",
                "uri": "frontend:latest",
                "tag": FRONTEND_REVISION,
            },
            {"digest": "sha256:untraced", "uri": "frontend:dev", "tag": "dev"},
        ],
    )
    neo4j_session.run(
        """
        MATCH (list:AWSECRImage {id: 'sha256:build-id-tagged'})
        REMOVE list:Image
        SET list:ImageManifestList, list.type = 'manifest_list'
        MERGE (list)-[:CONTAINS_IMAGE]->(:AWSECRImage:Image {
            id: 'sha256:build-id-amd64', digest: 'sha256:build-id-amd64', type: 'image'
        })
        MERGE (repo:GitHubRepository {id: $repo_url})
        MERGE (other:GitHubRepository {id: 'https://github.com/example/other'})
        WITH other
        MATCH (img:AWSECRImage {id: 'sha256:provenance-matched'})
        MERGE (img)-[r:PACKAGED_FROM]->(other)
        SET r.match_method = 'provenance', r.lastupdated = $update_tag
        """,
        repo_url=FRONTEND_REPO,
        update_tag=TEST_UPDATE_TAG,
    )


def test_sync_links_images_to_codebuild_projects(mocker, neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    boto3_session = MagicMock()
    boto3_session.get_partition_for_region.return_value = "aws"
    boto3_session.get_available_regions.return_value = [TEST_REGION]
    create_test_account(neo4j_session, TEST_ACCOUNT_ID, TEST_UPDATE_TAG)
    _create_ecr_images(neo4j_session)
    mocker.patch.object(
        cartography.intel.aws.codebuild,
        "get_all_codebuild_projects",
        return_value=GET_PROJECTS,
    )
    mocker.patch.object(
        cartography.intel.aws.codebuild_supply_chain,
        "get_builds",
        return_value=GET_BUILDS,
    )
    common_job_parameters = {"UPDATE_TAG": TEST_UPDATE_TAG, "AWS_ID": TEST_ACCOUNT_ID}

    # Act
    sync(
        neo4j_session,
        boto3_session,
        [TEST_REGION],
        TEST_ACCOUNT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )
    run_typed_analysis_job(
        CODEBUILD_IMAGE_PACKAGED_FROM,
        neo4j_session,
        common_job_parameters,
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "AWSECRImage",
        "digest",
        "AWSCodeBuildProject",
        "arn",
        "PACKAGED_BY",
    ) == {
        ("sha256:build-id-tagged", FRONTEND_PROJECT_ARN),
        ("sha256:revision-tagged", FRONTEND_PROJECT_ARN),
        ("sha256:provenance-matched", FRONTEND_PROJECT_ARN),
    }
    packaged_from = neo4j_session.run(
        """
        MATCH (img:Image)-[r:PACKAGED_FROM]->(repo:GitHubRepository)
        RETURN img.digest AS digest, repo.id AS repo, r.match_method AS method,
               r.source_revision AS revision
        """
    ).data()
    assert {tuple(row.values()) for row in packaged_from} == {
        # The tag points at a manifest list, which is not an Image; its platform
        # image inherits the match.
        (
            "sha256:build-id-amd64",
            FRONTEND_REPO,
            "codebuild_build_id_tag",
            FRONTEND_REVISION,
        ),
        (
            "sha256:revision-tagged",
            FRONTEND_REPO,
            "codebuild_tag_revision",
            FRONTEND_PREVIOUS_REVISION,
        ),
        # A stronger matcher already claimed this image, so CodeBuild does not add a second repo.
        (
            "sha256:provenance-matched",
            "https://github.com/example/other",
            "provenance",
            None,
        ),
    }


def test_analysis_removes_codebuild_packaged_from_without_basis(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (img:AWSECRImage:Image {id: 'sha256:stale', digest: 'sha256:stale'})
        CREATE (repo:GitHubRepository {id: $repo_url})
        CREATE (img)-[:PACKAGED_FROM {
            match_method: 'codebuild_build_id_tag', lastupdated: $stale_tag
        }]->(repo)
        CREATE (img)-[:PACKAGED_FROM {
            match_method: 'dockerfile', lastupdated: $stale_tag
        }]->(:GitHubRepository {id: 'https://github.com/example/other'})
        """,
        repo_url=FRONTEND_REPO,
        stale_tag=TEST_UPDATE_TAG - 1,
    )

    # Act
    run_typed_analysis_job(
        CODEBUILD_IMAGE_PACKAGED_FROM,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert check_rels(
        neo4j_session,
        "Image",
        "digest",
        "GitHubRepository",
        "id",
        "PACKAGED_FROM",
    ) == {("sha256:stale", "https://github.com/example/other")}


def test_analysis_skips_images_whose_codebuild_repositories_disagree(neo4j_session):
    # Arrange
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    neo4j_session.run(
        """
        CREATE (img:AWSECRImage:Image {id: 'sha256:shared', digest: 'sha256:shared'})
        CREATE (:GitHubRepository {id: $github_url})
        CREATE (:GitLabProject {web_url: $gitlab_url})
        CREATE (img)-[:PACKAGED_BY {
            source_uri: $github_url, source_provider: 'github',
            match_method: 'codebuild_build_id_tag'
        }]->(:AWSCodeBuildProject {id: 'project-in-account-a'})
        CREATE (img)-[:PACKAGED_BY {
            source_uri: $gitlab_url, source_provider: 'gitlab',
            match_method: 'codebuild_build_id_tag'
        }]->(:AWSCodeBuildProject {id: 'project-in-account-b'})
        """,
        github_url=FRONTEND_REPO,
        gitlab_url="https://gitlab.com/example/frontend",
    )

    # Act
    run_typed_analysis_job(
        CODEBUILD_IMAGE_PACKAGED_FROM,
        neo4j_session,
        {"UPDATE_TAG": TEST_UPDATE_TAG},
    )

    # Assert
    assert (
        neo4j_session.run(
            "MATCH (:Image)-[r:PACKAGED_FROM]->() RETURN count(r) AS n"
        ).single()["n"]
        == 0
    )
