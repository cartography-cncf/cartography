from collections.abc import Callable
from datetime import datetime
from datetime import timezone
from functools import partial
from typing import Any
from unittest.mock import patch

import neo4j
import pytest

from cartography.client.core.tx import load
from cartography.intel.github.supply_chain import (
    get_unmatched_container_images_with_history,
)
from cartography.intel.gitlab.supply_chain import (
    get_unmatched_gitlab_container_images_with_history,
)
from cartography.intel.supply_chain import ContainerImage
from cartography.intel.supply_chain import get_unmatched_gcp_images_with_history
from cartography.intel.supply_chain import get_unmatched_scaleway_images_with_history
from cartography.models.aws.ecr.image_layer import ECRImageLayerNodeSchema
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.gcp.artifact_registry.image_layer import (
    GCPArtifactRegistryImageLayerSchema,
)
from cartography.models.github.container_image_layers import (
    GitHubContainerImageLayerSchema,
)
from cartography.models.gitlab.container_image_layers import (
    GitLabContainerImageLayerSchema,
)
from cartography.models.scaleway.container_registry.image_layer import (
    ScalewayContainerRegistryImageLayerSchema,
)


@pytest.fixture
def image_graph(neo4j_session):
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()
    yield neo4j_session
    neo4j_session.run("MATCH (n) DETACH DELETE n").consume()


@pytest.fixture(
    params=[
        (ECRImageLayerNodeSchema(), {"AWS_ID": "account"}),
        (GCPArtifactRegistryImageLayerSchema(), {"PROJECT_ID": "project"}),
        (GitHubContainerImageLayerSchema(), {"org_url": "https://github.com/example"}),
        (
            GitLabContainerImageLayerSchema(),
            {"org_id": 1, "gitlab_url": "https://gitlab.example.com"},
        ),
        (ScalewayContainerRegistryImageLayerSchema(), {"PROJECT_ID": "project"}),
    ],
    ids=["aws", "gcp", "github", "gitlab", "scaleway"],
)
def layer_schema(request):
    return request.param


def test_provider_layers_use_diff_id_as_indexed_identity(
    image_graph: neo4j.Session,
    layer_schema: tuple[CartographyNodeSchema, dict[str, Any]],
) -> None:
    # Arrange
    schema, scope = layer_schema
    layer = {
        "diff_id": "sha256:layer",
        "history": "RUN echo hello",
        "is_empty": False,
        "next_diff_ids": [],
    }

    # Act
    load(image_graph, schema, [layer], lastupdated=1, **scope)

    # Assert
    assert image_graph.run(
        "MATCH (layer:ImageLayer {id:$diff_id}) RETURN layer.diff_id AS diff_id, layer.history AS history",
        diff_id=layer["diff_id"],
    ).data() == [{"diff_id": "sha256:layer", "history": "RUN echo hello"}]
    assert (
        image_graph.run(
            "SHOW INDEXES YIELD labelsOrTypes, properties "
            "WHERE labelsOrTypes = ['ImageLayer'] AND properties = ['id'] "
            "RETURN count(*) AS count"
        ).single()["count"]
        == 1
    )


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
        CREATE (:ImageLayer {
            id: 'layer-' + toString(j), diff_id: 'layer-' + toString(j),
            history: $history, is_empty: false
        })
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


@pytest.fixture(
    params=[
        (
            partial(
                get_unmatched_container_images_with_history, organization="example"
            ),
            "ContainerRegistry",
            "ImageTag",
            "Image",
            "GitHubOrganization",
            "example",
        ),
        (
            partial(
                get_unmatched_gitlab_container_images_with_history,
                organization_id=1,
                gitlab_url="https://gitlab.example.com",
            ),
            "ContainerRegistry",
            "ImageTag",
            "Image",
            "GitLabOrganization",
            1,
        ),
        (
            partial(
                get_unmatched_gcp_images_with_history,
                sub_resource_label="GitHubOrganization",
                sub_resource_id="example",
            ),
            "GCPArtifactRegistryRepository",
            "GCPArtifactRegistryRepositoryImage",
            "Image:GCPArtifactRegistryImage",
            "GitHubOrganization",
            "example",
        ),
        (
            partial(
                get_unmatched_scaleway_images_with_history,
                sub_resource_label="GitHubOrganization",
                sub_resource_id="example",
            ),
            "ScalewayContainerRegistryNamespace",
            "ScalewayContainerRegistryImageTag",
            "Image:ScalewayContainerRegistryImage",
            "GitHubOrganization",
            "example",
        ),
    ],
    ids=["github", "gitlab", "gcp", "scaleway"],
)
def image_query(request):
    return request.param


def test_image_selection_bounds_tag_fanout_and_uses_layer_index(
    image_graph: neo4j.Session,
    image_query: tuple[
        Callable[..., list[ContainerImage]], str, str, str, str, str | int
    ],
) -> None:
    # Arrange
    get_images, registry_label, tag_label, image_label, scope, scope_id = image_query
    candidates: list[dict[str, Any]] = [
        {"group": "large", "id": f"large-{i}", "tag": f"v{i}", "time": i}
        for i in range(2000)
    ]
    candidates.extend(
        [
            {"group": "latest", "id": "latest-old", "tag": "latest", "time": 1},
            {"group": "latest", "id": "latest-new", "tag": "latest", "time": 2},
            {"group": "latest", "id": "latest-version", "tag": "v3", "time": 3},
            {"group": "null", "id": "null-time", "tag": "v1", "time": None},
            {"group": "null", "id": "dated", "tag": "v2", "time": 2},
            {"group": "null-tag", "id": "unnamed", "tag": None, "time": 3},
            {"group": "null-tag", "id": "named", "tag": "v2", "time": 2},
            {"group": "eligible", "id": "no-layers", "tag": "latest", "time": 6},
            {"group": "eligible", "id": "empty-layers", "tag": "latest", "time": 5},
            {"group": "eligible", "id": "current", "tag": "latest", "time": 4},
            {"group": "eligible", "id": "foreign", "tag": "latest", "time": 3},
            {"group": "eligible", "id": "stale", "tag": "latest", "time": 2},
            {"group": "eligible", "id": "fallback", "tag": "v1", "time": 1},
            {"group": "tie", "id": "tie-a", "tag": "v1", "time": None},
            {"group": "tie", "id": "tie-b", "tag": "v2", "time": None},
            {
                "group": "datetime",
                "id": "date-old",
                "tag": "v1",
                "time": datetime(2026, 1, 1, tzinfo=timezone.utc),
            },
            {
                "group": "datetime",
                "id": "date-new",
                "tag": "v2",
                "time": datetime(2026, 1, 2, tzinfo=timezone.utc),
            },
        ]
    )
    image_graph.run(
        f"""
        UNWIND $candidates AS candidate
        MERGE (repo:{registry_label} {{id: candidate.group}})
        SET repo.uri = candidate.group
        CREATE (tag:{tag_label} {{
            id: candidate.id, uri: candidate.id, image_name: 'app',
            tag: candidate.tag, name: candidate.tag,
            image_pushed_at: candidate.time, created_at: candidate.time,
            upload_time: candidate.time, updated_at: candidate.time
        }})
        CREATE (img:{image_label} {{
            id: candidate.id, digest: candidate.id,
            layer_diff_ids: ['layer-0', 'missing', 'layer-0', 'layer-1']
        }})
        CREATE (repo)-[:REPO_IMAGE]->(tag)-[:IMAGE]->(img)
        """,
        candidates=candidates,
    ).consume()
    image_graph.run(
        "MATCH (img:Image {id:'no-layers'}) REMOVE img.layer_diff_ids"
    ).consume()
    image_graph.run(
        "MATCH (img:Image {id:'empty-layers'}) SET img.layer_diff_ids = []"
    ).consume()
    image_graph.run(
        """
        UNWIND ['current', 'foreign', 'stale'] AS id
        MATCH (img:Image {id:id})
        CREATE (img)-[:PACKAGED_FROM {
            lastupdated: CASE WHEN id = 'current' THEN 1 ELSE 0 END,
            _sub_resource_label: $scope,
            _sub_resource_id: CASE WHEN id = 'foreign' THEN 'other' ELSE $scope_id END
        }]->(:SourceRepository)
        """,
        scope=scope,
        scope_id=scope_id,
    ).consume()
    image_graph.run(
        """
        UNWIND range(0, 999) AS i
        CREATE (:ImageLayer {
            id: 'layer-' + toString(i), diff_id: 'layer-' + toString(i),
            history: 'RUN echo ' + toString(i), is_empty: false
        })
        """,
    ).consume()
    image_graph.run(
        "CREATE INDEX IF NOT EXISTS FOR (layer:ImageLayer) ON (layer.id)"
    ).consume()
    image_graph.run("CALL db.awaitIndexes()").consume()

    # Act
    with patch.object(image_graph, "run", wraps=image_graph.run) as run:
        images = get_images(image_graph, update_tag=1)
    query, parameters = run.call_args.args[0], run.call_args.kwargs
    plan = image_graph.run("EXPLAIN " + query, **parameters).consume().plan
    repeated_images = get_images(image_graph, update_tag=1)

    # Assert
    digests = {image.digest for image in images}
    assert digests - {"tie-a", "tie-b"} == {
        "large-1999",
        "latest-new",
        "null-time",
        "unnamed",
        "stale",
        "date-new",
    }
    assert len(digests & {"tie-a", "tie-b"}) == 1
    assert len(images) == 7
    assert digests == {image.digest for image in repeated_images}
    expected_history = [
        {"diff_id": "layer-0", "created_by": "RUN echo 0", "empty_layer": False},
        {"diff_id": "missing", "created_by": "", "empty_layer": False},
        {"diff_id": "layer-0", "created_by": "RUN echo 0", "empty_layer": False},
        {"diff_id": "layer-1", "created_by": "RUN echo 1", "empty_layer": False},
    ]
    assert all(image.layer_history == expected_history for image in images)
    pending = [plan]
    layer_index_used = False
    while pending:
        operator = pending.pop()
        details = operator["args"].get("Details", "")
        # Layer ordering remains per image; candidate sorting would grow with tags.
        if operator["operatorType"].split("@")[0] == "Sort":
            assert "idx" in details
        assert "collect({" not in details
        if "IndexSeek" in operator["operatorType"] and "ImageLayer(id)" in details:
            layer_index_used = True
        pending.extend(operator.get("children", []))
    assert layer_index_used
