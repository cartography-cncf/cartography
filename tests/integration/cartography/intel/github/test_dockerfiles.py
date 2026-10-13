from unittest.mock import patch

import pytest

import cartography.intel.github.supply_chain
from tests.data.github.dockerfiles import DOCKERFILE_CONTENT
from tests.data.github.dockerfiles import TEST_REPOS

TEST_UPDATE_TAG = 123456789
TEST_JOB_PARAMS = {"UPDATE_TAG": TEST_UPDATE_TAG}
TEST_GITHUB_URL = "https://api.github.com/graphql"


@pytest.fixture
def isolated_neo4j_session(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    yield neo4j_session
    neo4j_session.run("MATCH (n) DETACH DELETE n")


@patch("cartography.intel.github.supply_chain.get_dockerfiles_for_repos")
@patch(
    "cartography.intel.github.supply_chain.get_unmatched_container_images_with_history"
)
@patch("cartography.intel.github.supply_chain.match_images_to_dockerfiles")
def test_sync_with_dockerfiles(
    mock_match,
    mock_get_unmatched_images,
    mock_get_dockerfiles,
    neo4j_session,
):
    """
    Test the full sync function when Dockerfiles are found.
    """
    # Arrange
    mock_dockerfiles = [
        {
            "repo_url": "https://github.com/testorg/testrepo",
            "repo_name": "testorg/testrepo",
            "path": "Dockerfile",
            "content": DOCKERFILE_CONTENT,
        }
    ]
    mock_get_dockerfiles.return_value = mock_dockerfiles
    mock_get_unmatched_images.return_value = []  # No unmatched container images
    mock_match.return_value = []  # No matches

    # Act - sync now returns None
    cartography.intel.github.supply_chain.sync(
        neo4j_session=neo4j_session,
        token="test_token",
        api_url=TEST_GITHUB_URL,
        organization="testorg",
        update_tag=TEST_UPDATE_TAG,
        common_job_parameters=TEST_JOB_PARAMS,
        repos=TEST_REPOS,
    )

    # Assert - dockerfiles were fetched (unmatched images empty, so no matching called)
    mock_get_dockerfiles.assert_not_called()  # No unmatched images → no dockerfile search


def test_get_unmatched_container_images_applies_limit_before_layer_history(
    isolated_neo4j_session,
):
    prefix = "github-supply-chain-limit-regression"
    isolated_neo4j_session.run(
        """
        UNWIND range(0, 2) AS i
        CREATE (repo:ContainerRegistry {
            uri: $prefix + '/repo-' + toString(i),
            name: 'repo-' + toString(i)
        })
        CREATE (tag:ImageTag {
            tag: 'latest',
            uri: $prefix + '/repo-' + toString(i) + ':latest',
            image_pushed_at: i
        })
        CREATE (img:Image {
            digest: $prefix + '-image-' + toString(i),
            layer_diff_ids: [
                $prefix + '-layer-' + toString(i) + '-0',
                $prefix + '-layer-' + toString(i) + '-1'
            ],
            type: 'image',
            architecture: 'amd64',
            os: 'linux'
        })
        CREATE (repo)-[:REPO_IMAGE]->(tag)-[:IMAGE]->(img)
        WITH img, i
        UNWIND range(0, 1) AS layer_index
        CREATE (:ImageLayer {
            id: $prefix + '-layer-' + toString(i) + '-' + toString(layer_index),
            diff_id: $prefix + '-layer-' + toString(i) + '-' + toString(layer_index),
            history: 'RUN echo ' + toString(layer_index),
            is_empty: false
        })
        """,
        prefix=prefix,
    )

    with patch.object(
        isolated_neo4j_session,
        "run",
        wraps=isolated_neo4j_session.run,
    ) as run:
        images = cartography.intel.github.supply_chain.get_unmatched_container_images_with_history(
            isolated_neo4j_session,
            organization="example",
            update_tag=TEST_UPDATE_TAG,
            limit=2,
        )

    assert len(images) == 2
    assert len({image.digest for image in images}) == 2
    assert all(len(image.layer_history) == 2 for image in images)
    query = next(
        call.args[0] for call in run.call_args_list if "UNWIND range" in call.args[0]
    )
    assert query.index("LIMIT 2") < query.index("UNWIND range")
