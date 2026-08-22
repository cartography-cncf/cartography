import copy

import pytest

import cartography.intel.railway.deployments
import cartography.intel.railway.serviceinstances
import tests.data.railway.bundles
from cartography.analysis.ontology.analysis import RESOLVED_IMAGE_JOBS
from cartography.client.container_registry import RegistryTransientError
from cartography.util import run_typed_analysis_job
from tests.integration.cartography.intel.railway.test_projects import (
    _common_job_parameters,
)
from tests.integration.cartography.intel.railway.test_projects import TEST_PROJECT_ID
from tests.integration.cartography.intel.railway.test_projects import TEST_UPDATE_TAG
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    _RegistryClient,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    _sync_compute_tier,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import BUNDLES
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    POSTGRES_INSTANCE_ID,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    PRODUCTION_ENV_ID,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    WEB_INSTANCE_ID,
)
from tests.integration.cartography.intel.railway.test_serviceinstances import (
    WEB_SERVICE_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

WEB_DEPLOYMENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
POSTGRES_DEPLOYMENT_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TRIGGER_ID = "dt111111-1111-1111-1111-111111111111"
PINNED_DIGEST = f"sha256:{'9' * 64}"
OTHER_PINNED_DIGEST = f"sha256:{'8' * 64}"


@pytest.fixture(autouse=True)
def _clear_external_images(neo4j_session):
    neo4j_session.run(
        "MATCH (n:ExternalContainerImageReference) DETACH DELETE n",
    ).consume()
    neo4j_session.run("MATCH (n:ExternalContainerImage) DETACH DELETE n").consume()
    yield
    neo4j_session.run(
        "MATCH (n:ExternalContainerImageReference) DETACH DELETE n",
    ).consume()
    neo4j_session.run("MATCH (n:ExternalContainerImage) DETACH DELETE n").consume()


def _bundle_with_web_image(reference):
    bundle = copy.deepcopy(tests.data.railway.bundles.RAILWAY_PROJECT_BUNDLE)
    for instance in cartography.intel.railway.serviceinstances.iter_service_instances(
        bundle,
    ):
        if instance["id"] == WEB_INSTANCE_ID:
            instance["source"]["image"] = reference
    return {TEST_PROJECT_ID: bundle}


def _run_resolved_image_analysis(neo4j_session, update_tag=TEST_UPDATE_TAG):
    for job in RESOLVED_IMAGE_JOBS:
        run_typed_analysis_job(job, neo4j_session, {"UPDATE_TAG": update_tag})


def test_load_railway_deployments(neo4j_session):
    # Arrange
    _sync_compute_tier(neo4j_session)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )

    # Assert deployments exist with their status
    assert check_nodes(
        neo4j_session,
        "RailwayDeployment",
        ["id", "status", "static_url"],
    ) == {
        (WEB_DEPLOYMENT_ID, "SUCCESS", "web-production-abcde.up.railway.app"),
        (POSTGRES_DEPLOYMENT_ID, "SUCCESS", None),
    }

    # Assert the canonical ontology edge required for Container -> ComputeService
    assert check_rels(
        neo4j_session,
        "RailwayDeployment",
        "id",
        "RailwayServiceInstance",
        "id",
        "WORKLOAD_PARENT",
        rel_direction_right=True,
    ) == {
        (WEB_DEPLOYMENT_ID, WEB_INSTANCE_ID),
        (POSTGRES_DEPLOYMENT_ID, POSTGRES_INSTANCE_ID),
    }

    # Assert the Container ontology label
    assert check_nodes(neo4j_session, "Container", ["id"]) == {
        (WEB_DEPLOYMENT_ID,),
        (POSTGRES_DEPLOYMENT_ID,),
    }

    # And the project tenant edge
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayDeployment",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, WEB_DEPLOYMENT_ID),
        (TEST_PROJECT_ID, POSTGRES_DEPLOYMENT_ID),
    }


def test_digest_pinned_current_deployment_resolves_exact_image(neo4j_session):
    # Arrange
    bundles = _bundle_with_web_image(f"postgres@{PINNED_DIGEST}")
    external_images = _sync_compute_tier(neo4j_session, bundles=bundles)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        bundles,
        TEST_UPDATE_TAG,
        external_images,
    )
    _run_resolved_image_analysis(neo4j_session)

    # Assert
    assert check_rels(
        neo4j_session,
        "RailwayDeployment",
        "id",
        "ExternalContainerImage",
        "digest",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {(WEB_DEPLOYMENT_ID, PINNED_DIGEST)}
    assert check_rels(
        neo4j_session,
        "RailwayDeployment",
        "id",
        "ExternalContainerImage",
        "digest",
        "RESOLVED_IMAGE",
        rel_direction_right=True,
    ) == {(WEB_DEPLOYMENT_ID, PINNED_DIGEST)}


def test_failed_latest_deployment_has_no_container_or_runtime_image_evidence(
    neo4j_session,
):
    # Arrange
    bundles = _bundle_with_web_image(f"postgres@{PINNED_DIGEST}")
    bundle = bundles[TEST_PROJECT_ID]
    instances = cartography.intel.railway.serviceinstances.iter_service_instances(
        bundle
    )
    web = next(instance for instance in instances if instance["id"] == WEB_INSTANCE_ID)
    web["latestDeployment"]["status"] = "FAILED"
    for environment_edge in bundle["environments"]["edges"]:
        for deployment_edge in environment_edge["node"]["deployments"]["edges"]:
            deployment = deployment_edge["node"]
            if deployment["id"] == WEB_DEPLOYMENT_ID:
                deployment["status"] = "FAILED"
    external_images = _sync_compute_tier(neo4j_session, bundles=bundles)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        bundles,
        TEST_UPDATE_TAG,
        external_images,
    )
    _run_resolved_image_analysis(neo4j_session)

    # Assert
    assert check_nodes(neo4j_session, "RailwayDeployment", ["id", "lifecycle"]) == {
        (WEB_DEPLOYMENT_ID, "historical"),
        (POSTGRES_DEPLOYMENT_ID, "current"),
    }
    assert check_nodes(neo4j_session, "Container", ["id"]) == {
        (POSTGRES_DEPLOYMENT_ID,),
    }
    assert check_rels(
        neo4j_session,
        "RailwayServiceInstance",
        "id",
        "ExternalContainerImageReference",
        "id",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {
        (
            WEB_INSTANCE_ID,
            f"docker.io/library/postgres@{PINNED_DIGEST}",
        ),
    }
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeployment",
            "id",
            "ExternalContainerImage",
            "digest",
            "HAS_IMAGE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeployment",
            "id",
            "ExternalContainerImage",
            "digest",
            "RESOLVED_IMAGE",
            rel_direction_right=True,
        )
        == set()
    )


@pytest.mark.parametrize(
    ("second_reference", "expected_edges"),
    [
        (
            f"postgres@{PINNED_DIGEST}",
            {(WEB_DEPLOYMENT_ID, PINNED_DIGEST)},
        ),
        (f"postgres@{OTHER_PINNED_DIGEST}", set()),
    ],
    ids=("same-reference", "changed-reference"),
)
def test_registry_failure_preserves_only_matching_deployment_image_edge(
    neo4j_session,
    second_reference,
    expected_edges,
):
    # Arrange
    initial_bundles = _bundle_with_web_image(f"postgres@{PINNED_DIGEST}")
    external_images = _sync_compute_tier(
        neo4j_session,
        bundles=initial_bundles,
        update_tag=1,
    )
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(1),
        initial_bundles,
        1,
        external_images,
    )
    second_bundles = _bundle_with_web_image(second_reference)
    unresolved_images = _sync_compute_tier(
        neo4j_session,
        bundles=second_bundles,
        registry_client=_RegistryClient(RegistryTransientError("temporary failure")),
        update_tag=2,
    )

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(2),
        second_bundles,
        2,
        unresolved_images,
    )

    # Assert
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeployment",
            "id",
            "ExternalContainerImage",
            "digest",
            "HAS_IMAGE",
            rel_direction_right=True,
        )
        == expected_edges
    )


def test_mutable_tag_keeps_configured_reference_without_runtime_edge(neo4j_session):
    # Arrange
    bundles = _bundle_with_web_image("postgres:16")
    external_images = _sync_compute_tier(neo4j_session, bundles=bundles)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        bundles,
        TEST_UPDATE_TAG,
        external_images,
    )
    _run_resolved_image_analysis(neo4j_session)

    # Assert
    assert check_rels(
        neo4j_session,
        "RailwayServiceInstance",
        "id",
        "ExternalContainerImageReference",
        "id",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {(WEB_INSTANCE_ID, "docker.io/library/postgres:16")}
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeployment",
            "id",
            "ExternalContainerImage",
            "digest",
            "HAS_IMAGE",
            rel_direction_right=True,
        )
        == set()
    )
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeployment",
            "id",
            "ExternalContainerImage",
            "digest",
            "RESOLVED_IMAGE",
            rel_direction_right=True,
        )
        == set()
    )


def test_digest_pinned_index_without_runtime_platform_is_not_resolved(neo4j_session):
    # Arrange
    bundles = _bundle_with_web_image(f"postgres@{PINNED_DIGEST}")
    external_images = _sync_compute_tier(
        neo4j_session,
        bundles=bundles,
        registry_client=_RegistryClient(artifact_type="manifest_list"),
    )

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        bundles,
        TEST_UPDATE_TAG,
        external_images,
    )
    _run_resolved_image_analysis(neo4j_session)

    # Assert
    assert check_rels(
        neo4j_session,
        "RailwayDeployment",
        "id",
        "ExternalContainerImage",
        "digest",
        "HAS_IMAGE",
        rel_direction_right=True,
    ) == {(WEB_DEPLOYMENT_ID, PINNED_DIGEST)}
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeployment",
            "id",
            "Image",
            "digest",
            "RESOLVED_IMAGE",
            rel_direction_right=True,
        )
        == set()
    )


def test_load_railway_deployment_triggers(neo4j_session):
    # Arrange: the GitHub repo the trigger tracks.
    neo4j_session.run(
        """
        MERGE (r:GitHubRepository {id: "https://github.com/acme/api"})
        SET r.fullname = "acme/api", r.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )
    _sync_compute_tier(neo4j_session)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )

    # Assert the trigger exists
    assert check_nodes(
        neo4j_session,
        "RailwayDeploymentTrigger",
        ["id", "provider", "repository", "branch"],
    ) == {
        (TRIGGER_ID, "github", "acme/api", "main"),
    }

    # Assert it attaches to the service instance it deploys
    assert check_rels(
        neo4j_session,
        "RailwayServiceInstance",
        "id",
        "RailwayDeploymentTrigger",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (POSTGRES_INSTANCE_ID, TRIGGER_ID),
    }

    # Assert the cross-module link to the GitHub repo
    assert check_rels(
        neo4j_session,
        "RailwayDeploymentTrigger",
        "id",
        "GitHubRepository",
        "fullname",
        "TRACKS",
        rel_direction_right=True,
    ) == {
        (TRIGGER_ID, "acme/api"),
    }


def test_railway_deployment_trigger_no_edge_when_repo_absent(neo4j_session):
    # Arrange: no GitHubRepository ingested.
    neo4j_session.run("MATCH (r:GitHubRepository) DETACH DELETE r")
    _sync_compute_tier(neo4j_session)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )

    # Assert the trigger still lands; only the best-effort join is skipped.
    assert check_nodes(neo4j_session, "RailwayDeploymentTrigger", ["id"]) == {
        (TRIGGER_ID,),
    }
    assert (
        check_rels(
            neo4j_session,
            "RailwayDeploymentTrigger",
            "id",
            "GitHubRepository",
            "fullname",
            "TRACKS",
            rel_direction_right=True,
        )
        == set()
    )


def test_only_the_current_deployment_is_a_container(neo4j_session):
    """
    Railway keeps a row for every past deploy attempt, including FAILED and CRASHED ones.
    Labelling those Container would fill the cross-provider container ontology with things
    that are not running, so the label is conditional on the current revision.
    """
    neo4j_session.run("MATCH (d:RailwayDeployment) DETACH DELETE d")
    _sync_compute_tier(neo4j_session)

    # Act
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )

    # Both fixture deployments are the latestDeployment of their instance, so both are
    # current and both are Containers.
    assert check_nodes(neo4j_session, "RailwayDeployment", ["id", "lifecycle"]) == {
        (WEB_DEPLOYMENT_ID, "current"),
        (POSTGRES_DEPLOYMENT_ID, "current"),
    }
    assert check_nodes(neo4j_session, "Container", ["id"]) == {
        (WEB_DEPLOYMENT_ID,),
        (POSTGRES_DEPLOYMENT_ID,),
    }


def test_superseded_deployments_are_not_containers(neo4j_session):
    # A crashed revision that is no longer the instance's latestDeployment.
    neo4j_session.run("MATCH (d:RailwayDeployment) DETACH DELETE d")
    bundle = copy.deepcopy(tests.data.railway.bundles.RAILWAY_PROJECT_BUNDLE)
    for env_edge in bundle["environments"]["edges"]:
        env = env_edge["node"]
        if env["name"] != "production":
            continue
        env["deployments"]["edges"].append(
            {
                "node": {
                    "id": "cccc0000-cccc-cccc-cccc-cccccccccccc",
                    "status": "CRASHED",
                    "statusUpdatedAt": "2026-07-27T17:00:00.000Z",
                    "createdAt": "2026-07-27T17:00:00.000Z",
                    "projectId": TEST_PROJECT_ID,
                    "environmentId": PRODUCTION_ENV_ID,
                    "serviceId": WEB_SERVICE_ID,
                    "url": None,
                    "staticUrl": None,
                    "canRedeploy": True,
                },
            },
        )
    bundles = {TEST_PROJECT_ID: bundle}

    _sync_compute_tier(neo4j_session)
    cartography.intel.railway.deployments.sync(
        neo4j_session,
        _common_job_parameters(),
        bundles,
        TEST_UPDATE_TAG,
    )

    # The crashed revision is ingested for deploy history...
    assert check_nodes(neo4j_session, "RailwayDeployment", ["id", "lifecycle"]) == {
        (WEB_DEPLOYMENT_ID, "current"),
        (POSTGRES_DEPLOYMENT_ID, "current"),
        ("cccc0000-cccc-cccc-cccc-cccccccccccc", "historical"),
    }
    # ...but it is not a Container, and so is invisible to container ontology queries.
    assert check_nodes(neo4j_session, "Container", ["id"]) == {
        (WEB_DEPLOYMENT_ID,),
        (POSTGRES_DEPLOYMENT_ID,),
    }
