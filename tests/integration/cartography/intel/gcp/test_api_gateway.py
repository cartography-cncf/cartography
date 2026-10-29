from unittest.mock import MagicMock
from unittest.mock import patch

import cartography.intel.gcp.api_gateway
import tests.data.gcp.api_gateway
from tests.integration.util import check_nodes
from tests.integration.util import check_rels

TEST_UPDATE_TAG = 123456789
TEST_PROJECT_ID = "test-project-123"


def _sync_gateways_only(neo4j_session, gateways, incomplete, update_tag):
    with (
        patch.object(
            cartography.intel.gcp.api_gateway, "get_apis", return_value=([], False)
        ),
        patch.object(
            cartography.intel.gcp.api_gateway,
            "get_api_configs",
            return_value=([], False),
        ),
        patch.object(
            cartography.intel.gcp.api_gateway,
            "get_gateways",
            return_value=(gateways, incomplete),
        ),
    ):
        cartography.intel.gcp.api_gateway.sync(
            neo4j_session,
            MagicMock(),
            TEST_PROJECT_ID,
            update_tag,
            {"UPDATE_TAG": update_tag, "PROJECT_ID": TEST_PROJECT_ID},
        )


def test_cleanup_stays_in_its_project_and_waits_for_a_complete_listing(
    neo4j_session,
):
    """
    Cleanup must never touch another project's gateways, and must keep a gateway
    that only looks gone because a location was unreachable.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session)
    other = "projects/other-project/locations/us-east1/gateways/keep"
    neo4j_session.run(
        """
        MERGE (p:GCPProject{id: 'other-project'})
        MERGE (p)-[:RESOURCE]->(g:GCPApiGatewayGateway{id: $gw})
        SET g.lastupdated = 1
        """,
        gw=other,
    )
    gateways = tests.data.gcp.api_gateway.LIST_GATEWAYS_RESPONSE
    orders, internal = gateways[0]["name"], gateways[1]["name"]

    _sync_gateways_only(neo4j_session, gateways, False, 100)
    # internal-gw is missing, but the listing reported an unreachable location.
    _sync_gateways_only(neo4j_session, gateways[:1], True, 200)
    assert check_nodes(neo4j_session, "GCPApiGatewayGateway", ["id"]) == {
        (orders,),
        (internal,),
        (other,),
    }

    # Now the listing is complete, so internal-gw really is gone.
    _sync_gateways_only(neo4j_session, gateways[:1], False, 300)
    assert check_nodes(neo4j_session, "GCPApiGatewayGateway", ["id"]) == {
        (orders,),
        (other,),
    }


def _create_test_project(neo4j_session):
    neo4j_session.run(
        """
        MERGE (project:GCPProject{id: $project_id})
        ON CREATE SET project.firstseen = timestamp()
        SET project.lastupdated = $update_tag
        """,
        project_id=TEST_PROJECT_ID,
        update_tag=TEST_UPDATE_TAG,
    )


@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_gateways",
    return_value=(tests.data.gcp.api_gateway.LIST_GATEWAYS_RESPONSE, False),
)
@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_api_configs",
    return_value=(tests.data.gcp.api_gateway.LIST_API_CONFIGS_RESPONSE, False),
)
@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_apis",
    return_value=(tests.data.gcp.api_gateway.LIST_APIS_RESPONSE, False),
)
def test_sync_api_gateway(
    mock_get_apis, mock_get_api_configs, mock_get_gateways, neo4j_session
):
    """Sync loads all three API Gateway resource types and links them."""
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session)

    common_job_parameters = {
        "UPDATE_TAG": TEST_UPDATE_TAG,
        "PROJECT_ID": TEST_PROJECT_ID,
    }

    cartography.intel.gcp.api_gateway.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        common_job_parameters,
    )

    assert check_nodes(neo4j_session, "GCPApiGatewayApi", ["id", "state"]) == {
        (
            "projects/test-project-123/locations/global/apis/orders-api",
            "ACTIVE",
        ),
        (
            "projects/test-project-123/locations/global/apis/internal-api",
            "CREATING",
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPApiGatewayApiConfig",
        ["id", "has_openapi_document"],
    ) == {
        (
            "projects/123456789012/locations/global/apis/orders-api/configs/v1",
            True,
        ),
        (
            "projects/123456789012/locations/global/apis/internal-api/configs/v1",
            False,
        ),
    }

    assert check_nodes(
        neo4j_session,
        "GCPApiGatewayGateway",
        ["id", "default_hostname", "region"],
    ) == {
        (
            "projects/test-project-123/locations/us-central1/gateways/orders-gw",
            "orders-gw-1a2b3c.uc.gateway.dev",
            "us-central1",
        ),
        (
            "projects/test-project-123/locations/europe-west1/gateways/internal-gw",
            None,
            "europe-west1",
        ),
    }


@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_gateways",
    return_value=(tests.data.gcp.api_gateway.LIST_GATEWAYS_RESPONSE, False),
)
@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_api_configs",
    return_value=(tests.data.gcp.api_gateway.LIST_API_CONFIGS_RESPONSE, False),
)
@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_apis",
    return_value=(tests.data.gcp.api_gateway.LIST_APIS_RESPONSE, False),
)
def test_sync_api_gateway_relationships(
    mock_get_apis, mock_get_api_configs, mock_get_gateways, neo4j_session
):
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session)
    neo4j_session.run(
        """
        MERGE (sa:GCPServiceAccount{id: $sa_id})
        SET sa.email = $email, sa.lastupdated = $update_tag
        """,
        sa_id="sa-gw",
        email="gw@test-project-123.iam.gserviceaccount.com",
        update_tag=TEST_UPDATE_TAG,
    )

    cartography.intel.gcp.api_gateway.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "PROJECT_ID": TEST_PROJECT_ID},
    )

    assert check_rels(
        neo4j_session,
        "GCPProject",
        "id",
        "GCPApiGatewayGateway",
        "id",
        "RESOURCE",
    ) == {
        (
            TEST_PROJECT_ID,
            "projects/test-project-123/locations/us-central1/gateways/orders-gw",
        ),
        (
            TEST_PROJECT_ID,
            "projects/test-project-123/locations/europe-west1/gateways/internal-gw",
        ),
    }

    assert check_rels(
        neo4j_session,
        "GCPApiGatewayApi",
        "id",
        "GCPApiGatewayApiConfig",
        "id",
        "HAS_CONFIG",
    ) == {
        (
            "projects/test-project-123/locations/global/apis/orders-api",
            "projects/123456789012/locations/global/apis/orders-api/configs/v1",
        ),
        (
            "projects/test-project-123/locations/global/apis/internal-api",
            "projects/123456789012/locations/global/apis/internal-api/configs/v1",
        ),
    }

    # The config-to-service-account edge is the identity a gateway calls its
    # backends with, which is what an attack path through the gateway runs on.
    # Only the orders config names a service account; the other names none.
    assert check_rels(
        neo4j_session,
        "GCPApiGatewayApiConfig",
        "id",
        "GCPServiceAccount",
        "email",
        "USES_SERVICE_ACCOUNT",
    ) == {
        (
            "projects/123456789012/locations/global/apis/orders-api/configs/v1",
            "gw@test-project-123.iam.gserviceaccount.com",
        ),
    }

    # The gateway-to-config edge is what connects a public hostname to the
    # configuration that decides whether calls to it are authenticated.
    assert check_rels(
        neo4j_session,
        "GCPApiGatewayGateway",
        "id",
        "GCPApiGatewayApiConfig",
        "id",
        "USES_CONFIG",
    ) == {
        (
            "projects/test-project-123/locations/us-central1/gateways/orders-gw",
            "projects/123456789012/locations/global/apis/orders-api/configs/v1",
        ),
        (
            "projects/test-project-123/locations/europe-west1/gateways/internal-gw",
            "projects/123456789012/locations/global/apis/internal-api/configs/v1",
        ),
    }


@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_gateways",
    return_value=(tests.data.gcp.api_gateway.LIST_GATEWAYS_RESPONSE, False),
)
@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_api_configs",
    return_value=(tests.data.gcp.api_gateway.LIST_API_CONFIGS_RESPONSE, False),
)
@patch.object(
    cartography.intel.gcp.api_gateway,
    "get_apis",
    return_value=(tests.data.gcp.api_gateway.LIST_APIS_RESPONSE, False),
)
def test_sync_api_gateway_ontology_label(
    mock_get_apis, mock_get_api_configs, mock_get_gateways, neo4j_session
):
    """
    Deployed gateways carry the cross-provider APIGateway label and the
    normalized _ont_* fields. displayName is optional upstream, so _ont_name
    falls back to the resource name.
    """
    neo4j_session.run("MATCH (n) DETACH DELETE n")
    _create_test_project(neo4j_session)

    cartography.intel.gcp.api_gateway.sync(
        neo4j_session,
        MagicMock(),
        TEST_PROJECT_ID,
        TEST_UPDATE_TAG,
        {"UPDATE_TAG": TEST_UPDATE_TAG, "PROJECT_ID": TEST_PROJECT_ID},
    )

    assert check_nodes(
        neo4j_session,
        "APIGateway",
        ["id", "_ont_source", "_ont_name", "_ont_hostname"],
    ) == {
        (
            "projects/test-project-123/locations/us-central1/gateways/orders-gw",
            "gcp",
            "Orders Gateway",
            "orders-gw-1a2b3c.uc.gateway.dev",
        ),
        (
            "projects/test-project-123/locations/europe-west1/gateways/internal-gw",
            "gcp",
            "projects/test-project-123/locations/europe-west1/gateways/internal-gw",
            None,
        ),
    }
