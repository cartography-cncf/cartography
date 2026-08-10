import cartography.intel.railway.environments
import cartography.intel.railway.serviceinstances
import cartography.intel.railway.services
import tests.data.railway.bundles
import tests.data.railway.workspaces
from tests.integration.cartography.intel.railway.test_projects import (
    _common_job_parameters,
)
from tests.integration.cartography.intel.railway.test_projects import (
    _ensure_local_neo4j_has_test_workspace_and_projects,
)
from tests.integration.cartography.intel.railway.test_projects import TEST_PROJECT_ID
from tests.integration.cartography.intel.railway.test_projects import TEST_UPDATE_TAG
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

PRODUCTION_ENV_ID = "44444444-4444-4444-4444-444444444444"
STAGING_ENV_ID = "55555555-5555-5555-5555-555555555555"
WEB_SERVICE_ID = "66666666-6666-6666-6666-666666666666"
POSTGRES_SERVICE_ID = "77777777-7777-7777-7777-777777777777"
WEB_INSTANCE_ID = "88888888-8888-8888-8888-888888888888"
POSTGRES_INSTANCE_ID = "99999999-9999-9999-9999-999999999999"

BUNDLES = {TEST_PROJECT_ID: tests.data.railway.bundles.RAILWAY_PROJECT_BUNDLE}


def _sync_compute_tier(neo4j_session, tcp_proxies_by_instance=None):
    _ensure_local_neo4j_has_test_workspace_and_projects(neo4j_session)
    cartography.intel.railway.environments.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )
    cartography.intel.railway.services.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )
    cartography.intel.railway.serviceinstances.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        tcp_proxies_by_instance or {},
        tests.data.railway.workspaces.RAILWAY_WORKSPACE,
        TEST_UPDATE_TAG,
    )


def test_load_railway_environments_and_services(neo4j_session):
    # Act
    _sync_compute_tier(neo4j_session)

    # Assert environments exist and attach to their project
    assert check_nodes(
        neo4j_session,
        "RailwayEnvironment",
        ["id", "name", "is_ephemeral"],
    ) == {
        (STAGING_ENV_ID, "staging", False),
        (PRODUCTION_ENV_ID, "production", False),
    }
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayEnvironment",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, STAGING_ENV_ID),
        (TEST_PROJECT_ID, PRODUCTION_ENV_ID),
    }

    # Assert services exist and attach to their project
    assert check_nodes(neo4j_session, "RailwayService", ["id", "name"]) == {
        (WEB_SERVICE_ID, "web"),
        (POSTGRES_SERVICE_ID, "Postgres"),
    }
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayService",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, WEB_SERVICE_ID),
        (TEST_PROJECT_ID, POSTGRES_SERVICE_ID),
    }


def test_load_railway_service_instances(neo4j_session):
    # Act
    _sync_compute_tier(neo4j_session)

    # Assert instances carry the flattened source provenance
    assert check_nodes(
        neo4j_session,
        "RailwayServiceInstance",
        ["id", "service_name", "source_image", "source_repo"],
    ) == {
        (WEB_INSTANCE_ID, "web", "nginxdemos/hello", None),
        (POSTGRES_INSTANCE_ID, "Postgres", None, "acme/api"),
    }

    # Assert the flattened latestDeployment fields
    assert check_nodes(
        neo4j_session,
        "RailwayServiceInstance",
        ["id", "latest_deployment_status"],
    ) == {
        (WEB_INSTANCE_ID, "SUCCESS"),
        (POSTGRES_INSTANCE_ID, "SUCCESS"),
    }

    # Assert both containment edges: the service shell and the environment
    assert check_rels(
        neo4j_session,
        "RailwayService",
        "id",
        "RailwayServiceInstance",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (WEB_SERVICE_ID, WEB_INSTANCE_ID),
        (POSTGRES_SERVICE_ID, POSTGRES_INSTANCE_ID),
    }
    assert check_rels(
        neo4j_session,
        "RailwayEnvironment",
        "id",
        "RailwayServiceInstance",
        "id",
        "HAS",
        rel_direction_right=True,
    ) == {
        (PRODUCTION_ENV_ID, WEB_INSTANCE_ID),
        (PRODUCTION_ENV_ID, POSTGRES_INSTANCE_ID),
    }

    # Assert the ComputeService ontology label
    assert check_nodes(neo4j_session, "ComputeService", ["id"]) == {
        (WEB_INSTANCE_ID,),
        (POSTGRES_INSTANCE_ID,),
    }


def test_railway_service_instance_deployed_from_github_repository(neo4j_session):
    # Arrange: the GitHub repo the Postgres instance's source points at.
    neo4j_session.run(
        """
        MERGE (r:GitHubRepository {id: "https://github.com/acme/api"})
        SET r.fullname = "acme/api", r.lastupdated = $update_tag
        """,
        update_tag=TEST_UPDATE_TAG,
    )

    # Act
    _sync_compute_tier(neo4j_session)

    # Assert the edge forms only for the instance with a git source
    assert check_rels(
        neo4j_session,
        "RailwayServiceInstance",
        "id",
        "GitHubRepository",
        "fullname",
        "DEPLOYED_FROM",
        rel_direction_right=True,
    ) == {
        (POSTGRES_INSTANCE_ID, "acme/api"),
    }


def test_railway_service_instance_no_edge_when_repo_absent(neo4j_session):
    # Arrange: no GitHubRepository ingested at all.
    neo4j_session.run("MATCH (r:GitHubRepository) DETACH DELETE r")

    # Act
    _sync_compute_tier(neo4j_session)

    # Assert: the join is best-effort, so no edge and no error.
    assert (
        check_rels(
            neo4j_session,
            "RailwayServiceInstance",
            "id",
            "GitHubRepository",
            "fullname",
            "DEPLOYED_FROM",
            rel_direction_right=True,
        )
        == set()
    )


def test_railway_service_instance_exposure_flag(neo4j_session):
    # Act: no TCP proxies, so exposure comes purely from domains.
    _sync_compute_tier(neo4j_session)

    # web has a Railway-generated domain and a verified custom domain; Postgres has neither.
    assert check_nodes(
        neo4j_session,
        "RailwayServiceInstance",
        ["id", "is_publicly_exposed"],
    ) == {
        (WEB_INSTANCE_ID, True),
        (POSTGRES_INSTANCE_ID, False),
    }


def test_railway_service_instance_exposed_by_tcp_proxy(neo4j_session):
    # Act: Postgres has no domains at all, so only a TCP proxy can expose it.
    _sync_compute_tier(
        neo4j_session,
        tcp_proxies_by_instance={
            POSTGRES_INSTANCE_ID: [
                {
                    "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
                    "syncStatus": "ACTIVE",
                },
            ],
        },
    )

    assert check_nodes(
        neo4j_session,
        "RailwayServiceInstance",
        ["id", "is_publicly_exposed"],
    ) == {
        (WEB_INSTANCE_ID, True),
        (POSTGRES_INSTANCE_ID, True),
    }


def test_unverified_custom_domain_alone_is_not_exposure():
    # A custom domain that has not passed DNS verification does not resolve yet.
    bundle = {
        "environments": {
            "edges": [
                {
                    "node": {
                        "serviceInstances": {
                            "edges": [
                                {
                                    "node": {
                                        "id": "instance-1",
                                        "source": {},
                                        "latestDeployment": None,
                                        "domains": {
                                            "serviceDomains": [],
                                            "customDomains": [
                                                {
                                                    "id": "cd-1",
                                                    "status": {"verified": False},
                                                },
                                            ],
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ],
        },
    }

    result = cartography.intel.railway.serviceinstances.transform(
        {"project-1": bundle},
        {},
    )

    assert result["project-1"][0]["is_publicly_exposed"] is False
