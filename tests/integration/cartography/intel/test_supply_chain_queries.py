from collections.abc import Callable
from functools import partial
from unittest.mock import patch

import neo4j
import pytest

from cartography.intel.github.supply_chain import (
    get_unmatched_container_images_with_history,
)
from cartography.intel.gitlab.supply_chain import (
    get_unmatched_gitlab_container_images_with_history,
)
from cartography.intel.supply_chain import ContainerImage
from cartography.intel.supply_chain import get_unmatched_gcp_images_with_history
from cartography.intel.supply_chain import get_unmatched_scaleway_images_with_history


@pytest.fixture
def image_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    yield neo4j_session
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


def test_unlimited_github_images_aggregate_history_per_image(
    image_graph: neo4j.Session,
):
    _check_unlimited_image_history(
        image_graph,
        partial(get_unmatched_container_images_with_history, organization="example"),
        "ContainerRegistry",
        "ImageTag",
        "Image",
    )


def test_unlimited_gitlab_images_aggregate_history_per_image(
    image_graph: neo4j.Session,
):
    _check_unlimited_image_history(
        image_graph,
        partial(
            get_unmatched_gitlab_container_images_with_history,
            organization_id=1,
            gitlab_url="https://gitlab.example.com",
        ),
        "ContainerRegistry",
        "ImageTag",
        "Image",
    )


def test_unlimited_gcp_images_aggregate_history_per_image(image_graph: neo4j.Session):
    _check_unlimited_image_history(
        image_graph,
        partial(
            get_unmatched_gcp_images_with_history,
            sub_resource_label="GitHubOrganization",
            sub_resource_id="example",
        ),
        "GCPArtifactRegistryRepository",
        "GCPArtifactRegistryRepositoryImage",
        "Image:GCPArtifactRegistryImage",
    )


def test_unlimited_scaleway_images_aggregate_history_per_image(
    image_graph: neo4j.Session,
):
    _check_unlimited_image_history(
        image_graph,
        partial(
            get_unmatched_scaleway_images_with_history,
            sub_resource_label="GitHubOrganization",
            sub_resource_id="example",
        ),
        "ScalewayContainerRegistryNamespace",
        "ScalewayContainerRegistryImageTag",
        "Image:ScalewayContainerRegistryImage",
    )


def _check_unlimited_image_history(
    image_graph: neo4j.Session,
    get_images: Callable[..., list[ContainerImage]],
    registry_label: str,
    tag_label: str,
    image_label: str,
) -> None:
    # Arrange
    image_count = 32
    layer_count = 24
    history = "RUN echo " + "x" * 2048
    image_graph.run(
        f"""
        UNWIND range(0, $image_count - 1) AS i
        CREATE (repo:{registry_label} {{id: 'repo-' + toString(i), uri: 'repo-' + toString(i)}})
        CREATE (tag:{tag_label} {{
            id: 'tag-' + toString(i), uri: 'repo-' + toString(i) + ':latest',
            tag: 'latest', name: 'latest', image_name: 'app',
            image_pushed_at: i, created_at: i, upload_time: i, updated_at: i
        }})
        CREATE (img:{image_label} {{
            digest: 'image-' + toString(i),
            layer_diff_ids: [j IN range(0, $layer_count - 1) | 'layer-' + toString(j)]
        }})
        CREATE (repo)-[:REPO_IMAGE]->(tag)-[:IMAGE]->(img)
        """,
        image_count=image_count,
        layer_count=layer_count,
    ).consume()
    # Leave the final layer absent to check that OPTIONAL MATCH preserves its position.
    image_graph.run(
        """
        UNWIND range(0, $layer_count - 2) AS j
        CREATE (:ImageLayer {diff_id: 'layer-' + toString(j), history: $history, is_empty: false})
        """,
        layer_count=layer_count,
        history=history,
    ).consume()

    # Act
    with patch.object(image_graph, "run", wraps=image_graph.run) as run:
        images = get_images(image_graph, update_tag=1)
    query = run.call_args.args[0]
    parameters = run.call_args.kwargs

    # Assert
    assert {image.digest for image in images} == {
        f"image-{i}" for i in range(image_count)
    }
    assert len(images) == image_count
    expected_history = [
        {
            "diff_id": f"layer-{j}",
            "created_by": history if j < layer_count - 1 else "",
            "empty_layer": False,
        }
        for j in range(layer_count)
    ]
    assert all(image.layer_history == expected_history for image in images)

    # The compiled plan must aggregate inside the correlated subquery. A global
    # aggregation returns the same rows but retains every image's layer history.
    plan = image_graph.run("EXPLAIN " + query, **parameters).consume().plan
    pending = [(plan, False)]
    while pending:
        operator, in_subquery = pending.pop()
        details = operator["args"].get("Details", "")
        if in_subquery and "collect(layer_info) AS layer_history" in details:
            break
        # Apply's right branch is correlated; projections may precede aggregation.
        is_apply = operator["operatorType"].split("@")[0] == "Apply"
        pending.extend(
            (child, in_subquery or (is_apply and index == 1))
            for index, child in enumerate(operator.get("children", []))
        )
    else:
        pytest.fail("layer history is not aggregated per image")

    # Act and assert: explicit limits still bound images, not their layers.
    assert get_images(image_graph, update_tag=1, limit=0) == []
    limited_images = get_images(image_graph, update_tag=1, limit=2)
    assert len(limited_images) == 2
    assert all(image.layer_history == expected_history for image in limited_images)
