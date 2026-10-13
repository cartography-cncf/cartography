import cartography.intel.railway.network.domains
import cartography.intel.railway.network.tcpproxies
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
    WEB_INSTANCE_ID,
)
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

SERVICE_DOMAIN_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
VERIFIED_CUSTOM_DOMAIN_ID = "dc111111-1111-1111-1111-111111111111"
UNVERIFIED_CUSTOM_DOMAIN_ID = "dc222222-2222-2222-2222-222222222222"
WEB_PROXY_ID = "dddddddd-dddd-dddd-dddd-dddddddddddd"
POSTGRES_PROXY_ID = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
WEB_SERVICE_ID = "66666666-6666-6666-6666-666666666666"
POSTGRES_SERVICE_ID = "77777777-7777-7777-7777-777777777777"
PRODUCTION_ENV_ID = "44444444-4444-4444-4444-444444444444"

# Captured live via the aliased batch query; see cartography/intel/railway/utils.py.
TCP_PROXIES_BY_PROJECT = {
    TEST_PROJECT_ID: [
        {
            "id": WEB_PROXY_ID,
            "domain": "sakura.proxy.rlwy.net",
            "proxyPort": 54259,
            "applicationPort": 5432,
            "syncStatus": "ACTIVE",
            "createdAt": "2026-07-27T18:02:00.271Z",
            "service_id": WEB_SERVICE_ID,
            "environment_id": PRODUCTION_ENV_ID,
            "exposed_service_id": WEB_SERVICE_ID,
            "exposed_environment_id": PRODUCTION_ENV_ID,
        },
        {
            "id": POSTGRES_PROXY_ID,
            "domain": "tokaido.proxy.rlwy.net",
            "proxyPort": 23214,
            "applicationPort": 5432,
            "syncStatus": "ACTIVE",
            "createdAt": "2026-07-27T18:02:20.114Z",
            "service_id": POSTGRES_SERVICE_ID,
            "environment_id": PRODUCTION_ENV_ID,
            "exposed_service_id": POSTGRES_SERVICE_ID,
            "exposed_environment_id": PRODUCTION_ENV_ID,
        },
    ],
}


def test_load_railway_network(neo4j_session):
    """
    Service domains, custom domains and TCP proxies are loaded on top of one
    compute tier. Each set of assertions is filtered on its own entrypoint label,
    so loading domains and proxies together does not change any result.
    """
    # Arrange
    _sync_compute_tier(neo4j_session)

    # Act
    cartography.intel.railway.network.domains.sync(
        neo4j_session,
        _common_job_parameters(),
        BUNDLES,
        TEST_UPDATE_TAG,
    )
    cartography.intel.railway.network.tcpproxies.sync(
        neo4j_session,
        _common_job_parameters(),
        TCP_PROXIES_BY_PROJECT,
        TEST_UPDATE_TAG,
    )

    # Assert the Railway-generated domain exists and exposes its instance
    assert check_nodes(
        neo4j_session,
        "RailwayServiceDomain",
        ["id", "domain", "suffix"],
    ) == {
        (SERVICE_DOMAIN_ID, "web-production-abcde.up.railway.app", "up.railway.app"),
    }
    # EXPOSE points from the entrypoint to the asset it puts at risk.
    assert check_rels(
        neo4j_session,
        "RailwayServiceDomain",
        "id",
        "RailwayServiceInstance",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        (SERVICE_DOMAIN_ID, WEB_INSTANCE_ID),
    }

    # Assert the custom domains' nested `status` object is flattened onto the node
    assert check_nodes(
        neo4j_session,
        "RailwayCustomDomain",
        ["id", "domain", "verified", "certificate_status", "verification_dns_host"],
    ) == {
        (VERIFIED_CUSTOM_DOMAIN_ID, "app.example.com", True, "ISSUED", None),
        (
            UNVERIFIED_CUSTOM_DOMAIN_ID,
            "staging.example.com",
            False,
            "PENDING",
            "_railway.staging.example.com",
        ),
    }

    # Only the verified domain is a public entry point. An unverified one does not resolve,
    # so no EXPOSE edge: exposure traversals must agree with is_publicly_exposed.
    assert check_rels(
        neo4j_session,
        "RailwayCustomDomain",
        "id",
        "RailwayServiceInstance",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        (VERIFIED_CUSTOM_DOMAIN_ID, WEB_INSTANCE_ID),
    }

    # The unverified domain is still ingested and still records which instance it is meant
    # for, so nothing is lost by withholding the edge.
    assert check_nodes(
        neo4j_session,
        "RailwayCustomDomain",
        ["id", "service_id", "environment_id"],
    ) >= {
        (UNVERIFIED_CUSTOM_DOMAIN_ID, WEB_SERVICE_ID, PRODUCTION_ENV_ID),
    }

    # Assert TCP proxies exist with their published port
    assert check_nodes(
        neo4j_session,
        "RailwayTCPProxy",
        ["id", "domain", "proxy_port", "application_port"],
    ) == {
        (WEB_PROXY_ID, "sakura.proxy.rlwy.net", 54259, 5432),
        (POSTGRES_PROXY_ID, "tokaido.proxy.rlwy.net", 23214, 5432),
    }

    # Assert each proxy maps back to the right instance via its (service, environment) pair
    assert check_rels(
        neo4j_session,
        "RailwayTCPProxy",
        "id",
        "RailwayServiceInstance",
        "id",
        "EXPOSE",
        rel_direction_right=True,
    ) == {
        (WEB_PROXY_ID, WEB_INSTANCE_ID),
        (POSTGRES_PROXY_ID, POSTGRES_INSTANCE_ID),
    }

    # And to their project tenant
    assert check_rels(
        neo4j_session,
        "RailwayProject",
        "id",
        "RailwayTCPProxy",
        "id",
        "RESOURCE",
        rel_direction_right=True,
    ) == {
        (TEST_PROJECT_ID, WEB_PROXY_ID),
        (TEST_PROJECT_ID, POSTGRES_PROXY_ID),
    }
