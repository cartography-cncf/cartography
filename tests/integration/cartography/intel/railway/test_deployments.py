import copy

import cartography.intel.railway.deployments
import tests.data.railway.bundles
from tests.integration.cartography.intel.railway.test_projects import (
    _common_job_parameters,
)
from tests.integration.cartography.intel.railway.test_projects import TEST_PROJECT_ID
from tests.integration.cartography.intel.railway.test_projects import TEST_UPDATE_TAG
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
